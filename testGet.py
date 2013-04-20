#!/usr/bin/python
import glob
import os
import sys
import getopt
from lxml import etree
import shutil
import argparse
import sqlite3

testList = []
testNames = []
sourceDir = ""
destDir = ""
orgName = ""
uName = ""
pWord = ""
fullDestDir = ""
productionURL = "https://login.salesforce.com"
sandboxURL = "https://test.salesforce.com"

#collect options and validate they are correct

parser = argparse.ArgumentParser()

parser.add_argument("-s", help="Source directory to look for tests.")
parser.add_argument("-d", help="Destination directory for tests")
parser.add_argument("-n", help="Name of org, used to create subdir")
parser.add_argument("-c", help="Clean up dirs")
parser.add_argument("-x", help="makexml", action="store_true")
parser.add_argument("-db", help ="Add settings to db", action="store_true")
parser.add_argument("-l", help="List orgs", action="store_true")
parser.add_argument("-u", help="Username")
parser.add_argument("-p", help="Password")
parser.add_argument("-ip", help="Use production URL", action="store_true")

#Create the needed directory
def makeDir(destDir):
	try:
		os.makedirs(destDir + orgName + "/classes")
	except OSError:
		if not os.path.isdir(destDir):
			raise
	return(destDir)

#Create a subfolder for the name of the org
def getFullDestDir(destDir):
	fullDestDir = destDir + orgName + "/classes"
	return fullDestDir

#Search for testMethod string in classes
def searchTest(sourcedir):
	os.chdir(sourceDir)
	for files in glob.glob("*.*"):
		f=open(files, 'r')
		s=f.read()
		if 'testMethod' in s:
			testList.append(f.name)
			testList.append(f.name + "-meta.xml")
			testNames.append(os.path.splitext(f.name)[0])
	return {'testList':testList, 'testNames':testNames}

#Copy Tests to needed dir
def copyTest(testList):
	for x in testList:
        	shutil.copy2(sourceDir + x, getFullDestDir(destDir))

#checks if an org exists, if so return the needed variables
def getOrgInfo(orgName):
        conn = sqlite3.connect('orgs.db')
        c = conn.cursor()
        #find the org details
        c.execute("Select orgName, sourceDir, destDir, uName, pWord FROM main where orgName = ?", (orgName,))
        existingOrg = c.fetchall()
	# If org exists then return a map of its values
	if len(existingOrg) != 0:
		for row in existingOrg:
			orgName, sourceDir, destDir, uName, pWord = row
		return {'orgName':orgName, 'sourceDir':sourceDir, 'destDir':destDir, 'uName':uName, 'pWord':pWord} 
	# If it doesnt exist tell the user and exit
	else:
		print orgName + " doesnt exist"
		sys.exit(2)

#Remove the org from the db
def clean(orgName):
	# Call getOrgInfo and add needed values to variables
	cleanOrg = getOrgInfo(orgName)['orgName']
	destDir = getOrgInfo(orgName)['destDir']
	# If dictionary comes back not blank execute a delete
	if len(cleanOrg) != 0:
	        conn = sqlite3.connect('orgs.db')
	        c = conn.cursor()
                c.execute("DELETE FROM main where orgName = ?", (cleanOrg,))
                conn.commit()
                conn.close()
                shutil.rmtree(destDir + cleanOrg)
		print cleanOrg + " deleted"
	else:
		print cleanOrg + "does not exist"	

#todo, needs to output build.xml and package.xml
def buildXML(testNames, destDir, orgName, isProd, uName, pWord):
	buildNS = "antlib:com.salesforce"
	buildNsmap = {"sf": buildNS}
	build = etree.Element("project", name="Test Runner", default="test", basedir=".", nsmap=buildNsmap)
	target = etree.SubElement(build, "target", name="runTests")

	if isProd:
		deploy = etree.SubElement(target, "{antlib:com.salesforce}deploy", username=uName, password=pWord, serverurl=productionURL, deployRoot=".", maxPoll="7000", pollWaitMillis="8000", runAllTests="false", checkOnly="true")
	elif not isProd:
		deploy = etree.SubElement(target, "{antlib:com.salesforce}deploy", username=uName, password=pWord, serverurl=sandboxURL, deployRoot=".", maxPoll="7000", pollWaitMillis="8000", runAllTests="false", checkOnly="true")
	else:
		print "Bad value"

	for x in testNames:
		test = etree.SubElement(deploy, "runTest")
		test.text = x

	buildXML = etree.ElementTree(build)
	filepath = destDir + orgName + "/" #+ "build.xml"
	buildXML.write(filepath + "build.xml", pretty_print=True, xml_declaration=True)

	#create package.xml
	packageNS = "http://soap.sforce.com/2006/04/metadata"
	packageNsmap = { None : packageNS}
	package = etree.Element("Package", nsmap=packageNsmap)

	types = etree.SubElement(package, "types")

	for y in testNames:
		members = etree.SubElement(types, "members")
		members.text = y

	name = etree.SubElement(types, "name")
	name.text = "ApexClass"
	version = etree.SubElement(package, "version")
	version.text = "27.0"
	
	packageXML = etree.ElementTree(package)
	packageXML.write(filepath + "package.xml", pretty_print=True, xml_declaration=True)


#adds the org to the DB
def db(orgName, sourceDir, destDir, uName, pWord):
	#Create insert string
	orgList = (orgName, sourceDir, destDir, uName, pWord)
	#connect to DB
	conn = sqlite3.connect('orgs.db')
	c = conn.cursor()
	#create table if not exists and find org
	c.execute('''CREATE TABLE if not exists main(orgName, sourceDir, destDir, uName, pWord)''')
	c.execute("SELECT orgName FROM main WHERE orgName =?", (orgName,))
	existingOrg = c.fetchall()
	#if org exists dont create, if not, create
	if len(existingOrg) == 0:
		c.execute("INSERT INTO main VALUES (?,?,?,?,?)", orgList)
		print "Org %s added" % orgName
	else:
		print "Org %s already exists" % orgName

	conn.commit()
	conn.close()

#list orgs
def listOrgs():
	conn = sqlite3.connect('orgs.db')
	c = conn.cursor()
	c.execute("SELECT * FROM main")
	listOrgs = c.fetchall()
	if len(listOrgs) != 0:
		for line in listOrgs:
			print line 
	else:
		print "No orgs exists"

#select correct path
if __name__ == '__main__':
	args = parser.parse_args()
	sourceDir = args.s
	destDir = args.d
	orgName = args.n
	cleanOrg = args.c
	uName = args.u
	pWord = args.p
	if args.s and args.n and args.d and args.db and args.u and args.p:
		db(orgName, sourceDir, destDir, uName, pWord)
	elif args.c:
		clean(cleanOrg)
	elif args.l:
		listOrgs()
	elif args.n:
		if args.ip:
			sourceDir = getOrgInfo(orgName)['sourceDir']
                	destDir = getOrgInfo(orgName)['destDir']
			uName = getOrgInfo(orgName)['uName']
                	pWord = getOrgInfo(orgName)['pWord']
			testNames = searchTest(sourceDir)['testNames']
			isProd = True
                	makeDir(destDir)
                	searchTest(sourceDir)
                	copyTest(testList)
                	buildXML(testNames, destDir, orgName, isProd, uName, pWord)
		else:
			sourceDir = getOrgInfo(orgName)['sourceDir']
			destDir = getOrgInfo(orgName)['destDir']
                        uName = getOrgInfo(orgName)['uName']
                        pWord = getOrgInfo(orgName)['pWord']
			testNames = searchTest(sourceDir)['testNames']
			isProd = False
			makeDir(destDir)
                	searchTest(sourceDir)
                	copyTest(testList)
			buildXML(testNames, destDir, orgName, isProd, uName, pWord)
	else:
		print "Incorrect choice"







