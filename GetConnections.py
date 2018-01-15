'''
This script relies on the AdminWebservice POC
It loops through all the spaces that the user
has access to and returns a list of admin users
'''

from AdminWebservice import *
		
# Parameters to access webservice
domain = 'app2101.eu1.birst.com'
user_name = 'guillaume.loisel@schneider-electric.com'
password = 'xxxxx'

print 'Initiating application'

birst = WebService(domain, user_name, password)

spaces = birst.AdminClient.service.GetAllSpaces()

print 'Application successfully initiated'

print
print 'Retrieving the cluster information'
print

if len(spaces.SpacesList) > 0:
        
	for space in spaces.SpacesList[0]:
		
		birst.changeToSpace(space.SpaceID)
		conn = birst.AdminClient.service.getConnections()
		db_user = conn.Connection[0].UserName
		db_type = conn.Connection[0].Type

                cluster = '   '
                
                if db_user == 'acornaw_exa_db01':
                        cluster = 'Old'
                elif db_user == 'acornaw_exa_db03':
                        cluster = 'New'

                db_instance = '      '

                if db_type == 'Exasol':
                        db_instance = 'Exasol'
                else:
                        db_instance = 'SQLSrv'
                
		print cluster + ' | ' + db_instance + ' | ' + space.SpaceName
	
else:
	print 'Process finished, no space found'
	
print 'Exiting application'
birst.exitSession()
print 'Safe exit successful'
