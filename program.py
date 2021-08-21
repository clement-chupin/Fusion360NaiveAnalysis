import adsk.core, adsk.fusion, adsk.cam, traceback
from array import *
import sys
import time
#import mysql.connector


def run(context):
	ui = None
	try:
		app = adsk.core.Application.get()
		view = app.activeViewport
		ui = app.userInterface
		design = adsk.fusion.Design.cast(app.activeProduct)
		rootComp = design.rootComponent
		fileDialog = ui.createFileDialog()
		fileDialog.isMultiSelectEnabled = False
		fileDialog.title = "Specify result filename"
		fileDialog.filterIndex = 0
		dialogResult = fileDialog.showSave()
		if dialogResult == adsk.core.DialogResults.DialogOK:
			folder = fileDialog.filename
		else:
			sys.exit("problem : bad file input")
		dimensionMain=getDimXYZ(rootComp,ui)
		tab = getAllParameters(design)
		for i in range(len(tab)):
			min = 100000
			for j in range (len(tab[i][0])):
				if abs(tab[i][0][j]) < abs(min):
					min = tab[i][0][j]
			for j in range (len(tab[i][0])):
				if tab[i][0][j] == min:
					tab[i][2][j]=['0',0,min]
				else:
					tab[i][2][j]='-1'
		editTxt(folder,tab,dimensionMain)
		export3d(folder,rootComp,design)
		saveImage(view,folder)
		ui.messageBox('Done.')
	except:
		if ui:
			ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
def saveImage(view,folder):
	origine = adsk.core.Point3D.create(0, 0, 0)
	pov = adsk.core.Point3D.create(100, 100, 100)
	camera = view.camera
	camera.eye = pov
	camera.target = origine
	camera.perspectiveAngle = 0.6
	camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
	#camera.viewOrientation = 3
	camera.isFitView = True
	view.camera = camera
	#view.refresh()
	view.saveAsImageFile(folder+"_png", 0, 0)
def whichImpact(ui,design,nameValue):
	varA = 0.1
	varB = 0.1
	rootComp = design.rootComponent
	initGlob = getDimXYZ(rootComp,ui)
	initVal = design.allParameters.itemByName(nameValue).value 
	#time.sleep(0.5)
	design.allParameters.itemByName(nameValue).value = initVal+varA
	secondGlob = getDimXYZ(rootComp,ui)
	design.allParameters.itemByName(nameValue).value = initVal
	adsk.doEvents()
	ui.terminateActiveCommand()
	if initGlob == secondGlob:
		return '0'
	else:
		impact = "-1"
		a=0
		b=0
		for i in range(3):
			if getVal(initGlob,i) != getVal(secondGlob,i):
				impact = chr(ord('X') + i) 
			if getVal(secondGlob,i) - getVal(initGlob,i) == 0.1:
				a=1
			else:
				a= getVal(initGlob,i)/getVal(secondGlob,i) / 0.1
			b = initVal - getVal(initGlob,i)*a
		return [impact,a,b]
	sys.exit("problem : link of differents parts")
def getVal(point,index):
	if(index == 0):
		return point.x
	if(index == 1):
		return point.y
	if(index == 2):
		return point.z
	return -1
def getAllParameters(design):
	tab = [
			[
			[0,0,0],['','',''],
				[
				['',0,0],['',0,0],['',0,0]
				]
			]
		]
	nameParam = 'd'
	idParam = 1
	while design.allParameters.itemByName(nameParam+str(idParam)) is not None:
		value = design.allParameters.itemByName(nameParam+str(idParam))
		if value.value != 0:
			if('Sketch' in value.createdBy.classType()):
				if tab[len(tab)-1][0][1] == 0:
					tab[len(tab)-1][0][1] = value.value
					tab[len(tab)-1][1][1] = value.name
				else: 
					if tab[len(tab)-1][0][2] == 0:
						tab[len(tab)-1][0][2] = value.value
						tab[len(tab)-1][1][2] = value.name
					else:
						tab.append([[0,value.value,0],['',nameParam+str(idParam),''],[['',0,0],['',0,0],['',0,0]]])
			if('ExtrudeFeature' in value.createdBy.classType()):
				i = len(tab)-1
				while tab[i][0][0] == 0:
					tab[i][0][0] = value.value
					tab[i][1][0] = value.name
					i=i-1
		idParam = idParam+1
	return tab
def getDimXYZ(rootComp,ui):
	ui.terminateActiveCommand()
	boundingBox = rootComp.boundingBox
	boundingBox.maxPoint.x - boundingBox.minPoint.x
	boundingBox.maxPoint.y - boundingBox.minPoint.y
	boundingBox.maxPoint.z - boundingBox.minPoint.z
	return boundingBox.maxPoint
def getName(folder):
	tab = folder.split("/")
	return tab[len(tab)-1]
def editTxt(folder,tab,dimensionMain):
	f = open(folder+'_txt.txt', 'w')
	for i in range(len(tab)):
		f.write('planche n: '+str(i)+'\n')
		for j in range(len(tab[i][0])):
			#f.write(str(i)+str(j))
			f.write('   '+str(abs(tab[i][0][j])))
			f.write(' de la valeur :'+tab[i][1][j])
			f.write(' lié à :'+tab[i][2][j][0])
			#f.write(' par :'+str(tab[i][2][j][1]))
			#f.write(' et :'+str(tab[i][2][j][2]))
			f.write('\n')
	nameFold = getName(folder)
    
	f.write("\nINSERT INTO `contenu` (`id_meuble`,`image`,`globale_X`,`globale_Y`,`globale_Z`)")
	f.write(" VALUES ('"+nameFold+"','./meubles/"+nameFold+"_png.png','"+str(dimensionMain.x)+"','"+str(dimensionMain.y)+"','"+str(dimensionMain.z)+"');")
	for i in range(len(tab)):
		f.write("\nINSERT INTO `mesures` (`id_meuble`,`id_planche`,`x_id_valeur`,`y_id_valeur`,`z_id_valeur`) VALUES ('"+nameFold+"','planche:"+str(i)+"','0','1','2');")
		for j in range(len(tab[i][0])):
			f.write("\nINSERT INTO `valeur` (`a`,`b`, `id_planche`,`id_meuble`,`id_valeur`,`valeur_attache`,`valeur`) VALUES ('0','0','planche:"+str(i)+"','"+nameFold+"','"+str(j)+"','"+tab[i][1][j]+"','"+str(tab[i][0][j])+"');")
			#DELETE FROM `contenu`
	f.close()
def export3d(folder,rootComp,design):
	exportMgr = adsk.fusion.ExportManager.cast(design.exportManager)
	stlOptions = exportMgr.createSTLExportOptions(rootComp)
	stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
	stlOptions.filename = folder+"_stl"
	exportMgr.execute(stlOptions)

