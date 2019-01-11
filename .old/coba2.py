import numpy as np
import pandas as pd
from neo4j import GraphDatabase
from sklearn import preprocessing
from sklearn import tree
from subprocess import call
from IPython.display import Image

nodeStartedNonFreeChoice = []
nodeLeafNonFreeChoice = []
dataInArray = ""
dataTestingInArray = ""
dataTestingInArrayOneOfEachRow = []
dataLeafTestingEachNode = []
dataHeaderInArray = ""
dataLeaf = []
dataCaseActivity = []
dataCaseId = ""
nodeRoot = ["A"]
endNode = "H"

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "sanggung2"))

def deleteRelation(tx):
	tx.run("match p=()-[]-(), q=() delete p, q")

def deletenNode(tx, nodeName):
	tx.run("match (c:"+nodeName+") delete c")	

def importActivity(tx, fileName):
	tx.run("LOAD CSV with headers FROM 'file:///"+fileName+"' AS line "
			"Merge (:Activity {CaseId:line.Case_ID, Name:line.Activity, Time:line.Time})")

def importCaseActivity(tx, fileName):
	tx.run("LOAD CSV with headers FROM 'file:///"+fileName+"' AS line "
			"Merge (:CaseActivity {Name:line.Activity })")

def importCaseId(tx, fileName):
	tx.run("LOAD CSV with headers FROM 'file:///"+fileName+"' AS line "
			"Merge (:CaseId {Name:line.Case_ID })")

def createRelationship(tx):
	# create sequence relation
	tx.run("MATCH (c:Activity) "
			"WITH COLLECT(c) AS Caselist "
			"UNWIND RANGE(0,Size(Caselist) - 2) as idx "
			"WITH Caselist[idx] AS s1, Caselist[idx+1] AS s2 " 
			"MATCH (b:CaseActivity),(a:CaseActivity) "
			"WHERE s1.CaseId = s2.CaseId AND s1.Name = a.Name AND s2.Name = b.Name "
			"MERGE (a)-[r:SEQUENCE]->(b)")

	# create xorsplit relation
	tx.run("MATCH (bef)-[r]->(aft) "
		"WHERE size((bef)-->())>1 AND size((aft)<--())=1 AND ( size((aft)-->())=1 OR size((aft)-->())>1 ) "
		"CREATE (bef)-[:XORSPLIT]->(aft) "
		"DELETE r")

	# create xorjoin relation
	tx.run("MATCH (bef)-[r]->(aft) "
		"WHERE ( size((bef)-->())=1 OR size((bef)-->())>1 ) AND size((aft)<--())>1 " 
		"CREATE (bef)-[:XORJOIN]->(aft) "
		"DELETE r")

	# create andsplit relation
	tx.run("MATCH (aft1)<-[r]-(bef)-[s]->(aft2)"
		"WHERE size((bef)-->())>1 "
		"AND size((aft2)-->())=size((bef)-->()) AND size((aft1)-->())=size((bef)-->()) "
		"AND not (aft1)-[:SEQUENCE]->(bef) AND not (aft2)-[:SEQUENCE]->(bef) "
		"MERGE (aft1)<-[:ANDSPLIT]-(bef)-[:ANDSPLIT]->(aft2) "
		"DELETE r,s")

	# create andjoin relation
	tx.run("MATCH (aft1)-[r]->(bef)<-[s]-(aft2) "
		"WHERE size((bef)<--())>1 "
		"AND size((aft2)-->())=size((bef)<--()) AND size((aft1)-->())=size((bef)<--()) "
		"AND not ()-[:ANDSPLIT]->(bef) "
		"MERGE (aft1)-[:ANDJOIN]->(bef)<-[:ANDJOIN]-(aft2) "
		"DELETE r,s")

	# create Non-Free Choice
	tx.run("match ()-[c:XORSPLIT]->(n) "
		"match (a)-[b:XORJOIN]->() "
		"match (k:Activity),(l:Activity) "
		"where a.Name<>n.Name and k.Name=a.Name and l.Name=n.Name and k.CaseId=l.CaseId and k.Time<l.Time "
		"merge (a)-[:NONFREECHOICE]->(n)")

def createGraphEachCase(tx):
	tx.run("MATCH (ci:CaseId),(ca:Activity) "
			"WITH COLLECT(ci) AS CaseIdList, COLLECT(ca) AS CaseActivity "
			"UNWIND RANGE(0,Size(CaseIdList)-1) as cil "
			"UNWIND RANGE(0,Size(CaseActivity)- 1) as idx "
			"WITH CaseActivity[idx] AS s1, CaseActivity[idx+1] AS s2, CaseIdList[cil] as s3, CaseIdList[cil+1] as s4 "
			"ORDER BY s1.Time, s2.Time "
			"WHERE s1.CaseId = s2.CaseId  AND s1.CaseId = s3.Name AND s2.CaseId = s4.Name "
			"MERGE (s1)-[r:SEQUENCE]->(s2)") 

def printStartingNodeNonFreeChoice(tx):
	nodes = []
	global nodeStartedNonFreeChoice
	for record in tx.run("MATCH (p)-[r:XORSPLIT]->() RETURN p.Name ORDER BY p.Name"):
		nodes.append(record["p.Name"])
	nodeStartedNonFreeChoice = np.unique(np.array(nodes))
	return nodeStartedNonFreeChoice

def printActivityInCase(tx):
	nodes = []
	global dataCaseActivity
	for record in tx.run("MATCH (p:CaseId) return p.Name"):
		nodes.append(record["p.Name"])
	dataCaseActivity = np.unique(np.array(nodes))
	return dataCaseActivity

def printCaseId(tx):
	nodes = []
	global dataCaseId
	for record in tx.run("MATCH (p:CaseId) return p.Name"):
		nodes.append(record["p.Name"])
	dataCaseActivity = np.unique(np.array(nodes))
	return dataCaseActivity

def printActivitiesEachCase(tx, cashId):
	# MATCH  n = (a:Activity)--(b:Activity) Where a.CaseId <> "PP5" RETURN n
	for record in tx.run("MATCH (p)-[r:XORSPLIT]->() RETURN p.Name ORDER BY p.Name"):
		nodes.append(record["p.Name"])
	nodeStartedNonFreeChoice = np.unique(np.array(nodes))
	return nodeStartedNonFreeChoice

def printLeafNodeNonFreeChoice(tx):
	nodes = []
	global nodeLeafNonFreeChoice 
	for x in range(len(nodeStartedNonFreeChoice)):
		nodes = []
		for record in tx.run("MATCH (p)-[r:XORSPLIT]->(q) where p.Name = '"+nodeStartedNonFreeChoice[x]+"' return q.Name"):
			nodes.append(record["q.Name"])
		nodeLeafNonFreeChoice.append(nodes)
	nodeLeafNonFreeChoice = np.array(nodeLeafNonFreeChoice)
	return nodeLeafNonFreeChoice

def printLeafNode(tx):
	global nodeRoot
	global endNode
	traceRoot = []
	if nodeRoot[-1] != endNode:
		for record in tx.run("match p = (ac1:Activity)-->(ac2:Activity) where ac1.Name = '"+nodeRoot[-1]+"' return DISTINCT ac2.Name"):
			traceRoot.append(record["ac2.Name"])
	return traceRoot
		

def getDataInNonFreeChoice(fileName, types):
	global dataInArray
	global dataHeaderInArray
	global dataTestingInArray
	readData = pd.read_csv(fileName)
	if types == "dataTraining":
		dataHeaderInArray = np.array(readData.dtypes.index)
		dataInArray = np.array(readData)
		return dataInArray
	elif types == "dataTesting" :
		dataTestingInArray = np.array(readData)
		return dataTestingInArray

def getDataLeaf():
	global dataLeaf
	data1 = []
	for x in range(len(nodeStartedNonFreeChoice)):
		data2 = []
		for y in range(len(nodeLeafNonFreeChoice[x])):
			for z in range(len(dataInArray)):
				if nodeLeafNonFreeChoice[x][y] == dataInArray[z,-1]:
					data2.append(dataInArray[z])
		data1.append(data2)
	dataLeaf = np.array(data1)
	return dataLeaf

def calculateDecisionTree():
	for x in range(len(nodeStartedNonFreeChoice)):
		model = tree.DecisionTreeClassifier()
		dataModel = multipleEncodeLabel((np.array(dataLeaf[x][:, :5])), (np.array(dataLeaf[x][0, :5])))
		targetModel = singleEncodeLabel((dataLeaf[x][:, 5]))
		model.fit(dataModel, targetModel)
		
def createdVisualitationDecisionTree():
	for x in range(len(nodeStartedNonFreeChoice)):
		model = tree.DecisionTreeClassifier()
		dataModel = multipleEncodeLabel((np.array(dataLeaf[x][:, :5])), (np.array(dataLeaf[x][0, :5])))
		targetModel = singleEncodeLabel((dataLeaf[x][:, 5]))
		featureName = dataHeaderInArray[:5]
		targetName = leafNodeNonFreeChoice[x]

		estimator =  model.fit(dataModel, targetModel)

		tree.export_graphviz(estimator, out_file='tree'+str(x+1)+'a.dot', 
	                feature_names = featureName,
	                class_names = targetName,
	                rounded = True, proportion = False, 
	                precision = 2, filled = True)

		call(['dot', '-Tpng', 'tree'+str(x+1)+'a.dot', '-o', 'tree'+str(x+1)+'a.png', '-Gdpi=600'])
		Image(filename = 'tree'+str(x+1)+'a.png')

def multipleEncodeLabel(totalData, eachRowData):
	encodeDataLeaf = totalData
	le = preprocessing.LabelEncoder()
	for x in range(len(eachRowData)):
		dataModel = np.array(encodeDataLeaf[:, x])
		encodeDataLeaf[:, x] = le.fit_transform(dataModel) 

	return encodeDataLeaf

def singleEncodeLabel(totalData):
	encodeDataLeaf = totalData
	le = preprocessing.LabelEncoder()
	for x in range(len(encodeDataLeaf)):
		dataModel = np.array(encodeDataLeaf)
		encodeDataLeaf = le.fit_transform(dataModel) 

	return encodeDataLeaf

def changeTreeToLTL():
	pass

def resizeDataTesting():
	global dataTestingInArray
	global dataTestingInArrayOneOfEachRow
	data = []
	for x in range(len(dataCaseActivity)):
		data1 = []
		batas = np.where(dataTestingInArray[:,0] == np.array(dataCaseActivity[x]))
		for y in range(len(batas[0])):
			data1.append(dataTestingInArray[batas[0][y]])
		dataTestingInArrayOneOfEachRow.append(data1[0])
		data.append(data1)
	dataTestingInArray = np.array(data)
	return dataTestingInArray

def encodeDataTestingInArray(data):
	dataModel = multipleEncodeLabel((np.array(data[:, :5])), (np.array(data[0, :5])))
	return (dataModel)

# memperlukan node Leaf dan node root yang baru , data leaf dan data root ditrace pada setiap noode yang dijalani
def calculateDecisionTree():
	for x in range(len(nodeStartedNonFreeChoice)):
		model = tree.DecisionTreeClassifier()
		dataModel = multipleEncodeLabel((np.array(dataLeaf[x][:, :5])), (np.array(dataLeaf[x][0, :5])))
		targetModel = singleEncodeLabel((dataLeaf[x][:, 5]))
		model.fit(dataModel, targetModel)

		# merubah parameter testing
		dataTester = encodeDataTestingInArray(np.array(dataTestingInArrayOneOfEachRow))

# data leaf ini dubah untuk membaca setiap node yang ditrace
def getDataLeafTesting():
	global dataLeafTestingEachNode
	data1 = []
	for x in range(len(nodeRoot)):
		data2 = []
		for y in range(len(traceRoot[x])):
			for z in range(len(dataTestingInArray)):
				if traceRoot[x][y] == dataTestingInArray[z,-1]:
					data2.append(dataTestingInArray[z])
		data1.append(data2)
	dataLeafTestingEachNode = np.array(data1)
	return dataLeafTestingEachNode

with driver.session() as session:
    nameFileTraining = "nonfreechoice.csv"
    nameFIleTesting = "nfcWithError.csv"
    session.write_transaction(deleteRelation)
    session.write_transaction(deletenNode, "Activity")
    session.write_transaction(importActivity, nameFileTraining)
    session.write_transaction(importCaseActivity, nameFileTraining)
    session.write_transaction(createRelationship)
    session.write_transaction(deletenNode, "Activity")
    session.write_transaction(importActivity, nameFIleTesting)
    session.write_transaction(importCaseId, nameFIleTesting)
    session.write_transaction(createGraphEachCase)
    session.read_transaction(printActivityInCase)
    staringNonFreeChoice = session.read_transaction(printStartingNodeNonFreeChoice)
    leafNodeNonFreeChoice = session.read_transaction(printLeafNodeNonFreeChoice)
    getDataInNonFreeChoice(nameFileTraining, types="dataTraining")
    getDataInNonFreeChoice(nameFIleTesting, types="dataTesting")
    getDataLeaf()
    createdVisualitationDecisionTree()
    calculateDecisionTree()
    print(resizeDataTesting()[0])