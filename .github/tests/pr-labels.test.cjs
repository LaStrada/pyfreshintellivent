const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { test } = require('node:test');
const { join } = require('node:path');

const root = join(__dirname, '..');
const workflow = readFileSync(join(root, 'workflows/pr-labels.yml'), 'utf8');
// Execute the actual inline Actions script, without checking out PR code in that job.
const source = workflow.split('          script: |\n')[1]
  .split('\n').map(line => line.replace(/^ {12}/, '')).join('\n');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const run = new AsyncFunction('github', 'context', 'core', source);
const selection = text => `## Type of change\n- [x] ${text}\n`;

async function simulate(body, existing = [], options = {}) {
  const mutations = [];
  const failures = [];
  const infos = [];
  let pages = 0;
  const context = { repo: { owner: 'owner', repo: 'repo' }, payload: { pull_request: { number: 123, body: selection('Breaking change') } } };
  const github = {
    rest: {
      pulls: { get: async args => {
        assert.deepEqual(args, { owner: 'owner', repo: 'repo', pull_number: 123 });
        if (options.readError) throw options.readError;
        return { data: { body } };
      } },
      issues: {
        listLabelsOnIssue: Symbol('list labels'),
        addLabels: async args => {
          mutations.push(['add', args]);
          if (options.addError) throw options.addError;
        },
        removeLabel: async args => {
          mutations.push(['remove', args]);
          if (options.removeError) throw options.removeError;
        },
      },
    },
    paginate: async (method, args) => {
      pages++;
      assert.equal(method, github.rest.issues.listLabelsOnIssue);
      assert.deepEqual(args, { owner: 'owner', repo: 'repo', issue_number: 123, per_page: 100 });
      return existing.map(name => ({ name }));
    },
  };
  const core = { info: message => infos.push(message), setFailed: message => failures.push(message) };
  let error;
  try { await run(github, context, core); } catch (caught) { error = caught; }
  return { mutations, failures, infos, pages, error };
}

const mappings = [
  ['Bugfix', 'bug'],
  ['New feature or device support', 'enhancement'],
  ['Breaking change', 'breaking'],
  ['Dependency upgrade', 'dependencies'],
  ['Maintenance, tests, CI or documentation', 'maintenance'],
];
for (const [option, label] of mappings) {
  test(`template option applies ${label} from latest API body`, async () => {
    const template = readFileSync(join(root, 'PULL_REQUEST_TEMPLATE.md'), 'utf8');
    assert.ok(template.includes(`- [ ] ${option}`));
    const result = await simulate(template.replace(`- [ ] ${option}`, `- [x] ${option}`), ['research', 'testing']);
    assert.deepEqual(result.mutations, [['add', { owner: 'owner', repo: 'repo', issue_number: 123, labels: [label] }]]);
    assert.deepEqual(result.failures, []);
    assert.equal(result.error, undefined);
  });
}

test('switches only managed labels, adding before removal', async () => {
  const result = await simulate(selection('Bugfix'), ['enhancement', 'breaking', 'dependencies', 'maintenance', 'help wanted', 'research', 'documentation', 'testing']);
  assert.deepEqual(result.mutations.map(([op, args]) => [op, args.labels ?? args.name]), [
    ['add', ['bug']], ['remove', 'enhancement'], ['remove', 'breaking'], ['remove', 'dependencies'], ['remove', 'maintenance'],
  ]);
});

test('already correct labels are idempotent', async () => {
  const result = await simulate(selection('Bugfix'), ['bug', 'research']);
  assert.deepEqual(result.mutations, []);
  assert.equal(result.pages, 1);
});

for (const body of [null, '', 'Legacy PR', '## Type of change\n- [ ] Bugfix', '## Description\n- [x] Bugfix', '## Type of change\n### Validation\n- [x] Bugfix']) {
  test(`no selected type leaves labels untouched: ${JSON.stringify(body)}`, async () => {
    const result = await simulate(body, ['dependencies', 'python']);
    assert.deepEqual(result.mutations, []);
    assert.deepEqual(result.failures, []);
    assert.equal(result.pages, 0);
    assert.equal(result.infos.length, 1);
  });
}

for (const content of ['- [x] Bugfix\n- [x] Breaking change', '- [x] Unexpected option', '- [x] Bugfix\n- [x] Bugfix', '- [x] ${process.exit(1)}']) {
  test(`invalid selection fails without writes: ${content}`, async () => {
    const result = await simulate(`## Type of change\n${content}`, ['enhancement']);
    assert.equal(result.failures.length, 1);
    assert.deepEqual(result.mutations, []);
    assert.equal(result.pages, 0);
  });
}

test('supports CRLF, uppercase X, bullet stars and trailing heading hashes', async () => {
  const result = await simulate('  ## Type of change ##\r\n * [X] Bugfix   \r\n');
  assert.equal(result.mutations[0][1].labels[0], 'bug');
});

test('ignores HTML comments, fenced examples and selections outside the section', async () => {
  const result = await simulate([
    '<!--\n## Type of change\n- [x] Breaking change\n-->',
    '```md\n## Type of change\n- [x] Breaking change\n```',
    '## Type of change',
    '~~~md\n- [x] Breaking change\n```\n~~~',
    '````md\n- [x] Breaking change\n```\n````',
    '- [x] Bugfix',
    '## Validation\n- [x] Breaking change',
  ].join('\n'));
  assert.deepEqual(result.failures, []);
  assert.equal(result.mutations[0][1].labels[0], 'bug');
});

test('unterminated comment and fence cannot introduce a selection', async () => {
  for (const prefix of ['<!--', '```']) {
    const result = await simulate(`${prefix}\n${selection('Bugfix')}`);
    assert.deepEqual(result.mutations, []);
    assert.deepEqual(result.failures, []);
  }
});

test('API read failure makes no changes', async () => {
  const error = new Error('read failed');
  const result = await simulate(selection('Bugfix'), ['enhancement'], { readError: error });
  assert.equal(result.error, error);
  assert.deepEqual(result.mutations, []);
});

test('failed addition cannot erase the previous type', async () => {
  const error = new Error('write failed');
  const result = await simulate(selection('Bugfix'), ['enhancement'], { addError: error });
  assert.equal(result.error, error);
  assert.equal(result.mutations.length, 1);
  assert.equal(result.mutations[0][0], 'add');
});

test('already removed label is tolerated', async () => {
  const result = await simulate(selection('Bugfix'), ['bug', 'enhancement'], { removeError: { status: 404 } });
  assert.equal(result.error, undefined);
  assert.equal(result.mutations.length, 1);
});

test('other removal errors fail visibly', async () => {
  const error = { status: 403 };
  const result = await simulate(selection('Bugfix'), ['bug', 'enhancement'], { removeError: error });
  assert.equal(result.error, error);
});


for (const fence of ['```html', '~~~html', '```html <!-- literal']) {
  test(`comment markers inside ${fence} do not hide the real selection`, async () => {
    const body = ['## Description', fence, '<!-- unclosed example', fence.slice(0, 3), selection('Bugfix')].join('\n');
    const result = await simulate(body, ['enhancement', 'research']);
    assert.deepEqual(result.failures, []);
    assert.equal(result.error, undefined);
    assert.deepEqual(result.mutations.map(([op, args]) => [op, args.labels ?? args.name]), [
      ['add', ['bug']], ['remove', 'enhancement'],
    ]);
  });
}

test('fences inside comments remain comments and trailing comments are ignored', async () => {
  const body = [
    '<!-- hidden', '```md', selection('Breaking change'), '-->',
    '## Type of change',
    '- [x] Bugfix <!-- trailing -->',
  ].join('\n');
  const result = await simulate(body);
  assert.deepEqual(result.failures, []);
  assert.equal(result.error, undefined);
  assert.deepEqual(result.mutations.map(([op, args]) => [op, args.labels ?? args.name]), [['add', ['bug']]]);
});


for (const description of ['Use `<!--` to hide text', 'An unclosed <!-- inline marker', '    <!-- indented example', '\t<!-- tab-indented example']) {
  test(`literal comment in description does not hide the selection: ${description}`, async () => {
    const result = await simulate(`## Description\n\n${description}\n\n${selection('Bugfix')}`);
    assert.deepEqual(result.failures, []);
    assert.equal(result.error, undefined);
    assert.deepEqual(result.mutations.map(([op, args]) => [op, args.labels ?? args.name]), [['add', ['bug']]]);
  });
}

test('HTML comment blocks hide the entire closing line', async () => {
  const body = [
    '<!-- hidden', '-->## Type of change', '- [x] Breaking change',
    '## Type of change', '<!-- hidden -->- [x] Breaking change', '- [x] Bugfix',
  ].join('\n');
  const result = await simulate(body);
  assert.deepEqual(result.failures, []);
  assert.equal(result.error, undefined);
  assert.deepEqual(result.mutations.map(([op, args]) => [op, args.labels ?? args.name]), [['add', ['bug']]]);
});
