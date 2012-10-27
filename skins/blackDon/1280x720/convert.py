import os

def scale():
	scaleAttr = []
	scaleAttr.append(('xres="',           '"',  (scaleX, None  ), ))
	scaleAttr.append(('yres="',           '"',  (None,   scaleY), ))
	scaleAttr.append(('position="',       '"',  (scaleX, scaleY), ))
	scaleAttr.append(('size="',           '"',  (scaleX, scaleY), ))
	scaleAttr.append(('font="',           '"',  (None,   scaleY), ";", 1, ))
	scaleAttr.append(('pos = (',          ')',  (scaleX, scaleY), ))
	scaleAttr.append(('size = (',         ')',  (scaleX, scaleY), ))
	#scaleAttr.append(('"itemHeight": ',   ',',  (None,   scaleY), ))
	#scaleAttr.append(('"itemHeight":',    None, (None,   scaleY), ))
	scaleAttr.append(('"fonts": [gFont(', ')',  (None,   scaleY), ", ", 1, ))
	
	replace = []
	replace.append((str(int(orgX)) + "x" + str(int(orgY)), str(int(targetX)) + "x" + str(int(targetY)), ), )
	
	orgF = open("skin.xml", "r")
	targetF = open("skin_" + str(int(targetX)) + "x" + str(int(targetY)) + ".xml", "w+")
	for line in orgF.readlines():
		for rep in replace:
			line = line.replace(rep[0], rep[1])
		
		for attr in scaleAttr:
			posStart = line.find(attr[0])
			if posStart < 0:
				continue
			posStart = posStart + len(attr[0])
			#if attr[1] is not None:
			#	posEnd = line.find(attr[1], posStart)
			#else:
			#	posEnd = len(line)
			#if posEnd < 0:
			#	continue
			posEnd = line.find(attr[1], posStart)
			if posEnd < 0:
				posEnd = len(line)
			try:
				if attr[2][0] is not None and attr[2][1] is not None:
					orgValue = line[posStart:posEnd].split(",")
					orgValue[0] = orgValue[0].strip()
					orgValue[1] = orgValue[1].strip()
					if orgValue[0] == "center" and orgValue[1] == "center":
						newValue = "center,center"
					elif orgValue[0] == "center":
						newValue = "center,%d" % (int(orgValue[1]) * attr[2][1])
					elif orgValue[1] == "center":
						newValue = "%d,center" % (int(orgValue[0]) * attr[2][0])
					else:
						newValue = "%d,%d" % (int(orgValue[0]) * attr[2][0], int(orgValue[1]) * attr[2][1])
				elif attr[2][0] is not None:
					orgValue = line[posStart:posEnd].strip()
					
					if len(attr) > 3:
						pos = orgValue.find(attr[3])
						if pos < 0:
							continue
						index = 0
						if len(attr) > 4:
							index = attr[4]
						if index == 0:
							orgValue = orgValue[:pos]
							posEnd = posEnd + pos
						else:
							pos = pos + len(attr[3])
							orgValue = orgValue[pos:]
							posStart = posStart + pos
					
					if orgValue == "center":
						newValue = orgValue
					else:
						newValue = "%d" % (int(orgValue) * attr[2][0])
				elif attr[2][1] is not None:
					orgValue = line[posStart:posEnd].strip()
					
					if len(attr) > 3:
						pos = orgValue.find(attr[3])
						if pos < 0:
							continue
						index = 0
						if len(attr) > 4:
							index = attr[4]
						if index == 0:
							orgValue = orgValue[:pos]
							posEnd = posEnd + pos
						else:
							pos = pos + len(attr[3])
							orgValue = orgValue[pos:]
							posStart = posStart + pos
					
					if orgValue == "center":
						newValue = orgValue
					else:
						newValue = "%d" % (int(orgValue) * attr[2][1])
			except Exception, ex:
				print "Exception:", ex
				print "\tline:", line
				exit(0)
			newLine = line[:posStart] + newValue + line[posEnd:]
			line = newLine
		targetF.write(line)
	orgF.close()
	targetF.close()

orgX = 1280.0
orgY = 720.0


targetX = 720.0
targetY = 576.0
scaleX = targetX / orgX
scaleY = targetY / orgY
scale()

#259,267
#146,214

targetX = 1024.0
targetY = 576.0
scaleX = targetX / orgX
scaleY = targetY / orgY
scale()
