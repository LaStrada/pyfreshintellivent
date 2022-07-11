from pyfreshintellivent.pyfreshintellivent.FreshIntellivent import Sky
p = Sky(None,None,False)
p.connect("Adress here from scanner",None)
auth = p.fetchAuth()
print("Auth" , auth.hex() )
