'''
This script relies on the AdminWebservice POC
It loops through all the spaces that the user
has access to and returns a list of admin users
'''

from AdminWebservice import *
		
# Parameters to access webservice
domain = 'app2101.bws.birst.com'
user_name = 'guillaume.loisel@zodiacaerospace.com'
password = 'xxxx'

print 'Initiating application'

birst = WebService(domain, user_name, password)

spaces = birst.AdminClient.service.GetAllSpaces()

print 'Application successfully initiated'

print
print 'Retrieving the admin users'
print

if len(spaces.SpacesList) > 0:
	for space in spaces.SpacesList[0]:

		print space.SpaceName
		
		birst.changeToSpace(space.SpaceID)
		users = birst.AdminClient.service.GetSpaceShareDetails()
		
		currrent_user_found = False
		
		if len(users.SpaceAccessMembers) > 0:
			for user in users.SpaceAccessMembers[0]:

				if user.Admin:
					print '   ' + user.Username
				
				if user.Username == user_name:
					currrent_user_found = True
					
			if currrent_user_found is False:
				print '   ' + user_name
						
		else:
			print '   ' + user_name
	
else:
	print 'Process finished, no space found'
	
print 'Exiting application'
birst.exitSession()
print 'Safe exit successful'