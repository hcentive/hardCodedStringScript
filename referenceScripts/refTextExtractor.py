#!/usr/bin/python
 
# constants
##################################################
FILE_EXTENSIONS = '.jsp,'
 
# functions
##################################################
# process plain text
def process_text(text):
	global current_file_path, file_path_static_text_map
	text_strip = text.strip()
	if text_strip:
		file_path_static_text_map.setdefault(current_file_path, [])
		file_path_static_text_map[current_file_path].append(text)
 
# process a line
def process_line(l):
	str_parts = []
	global open_tags, open_el
	tmp_str=''
	print "line", l
	print "open_tags", open_tags
	print "open_el", open_el
	for i, char in enumerate(l):
		if open_el == -1:
			if char == '$':
				if i+1 < len(l) and l[i+1] == '{':
					if open_tags == 0:
						process_text(tmp_str)
					tmp_str = ''
					open_el = 0
				else:
					tmp_str += char
			elif char == '<':
				if open_tags == 0:
					process_text(tmp_str)
					tmp_str = ''
				else:
					tmp_str += char
				open_tags += 1
				print "open_tags in < loop", open_tags
			elif char == '>':
				tmp_str += char
				open_tags -= 1
				if open_tags == 0:
					tmp_str = ''
				print "open_tags in > loop", open_tags
			else:
				tmp_str += char
		else:
			if char == '{':
				open_el += 1
				#tmp_str += char
			elif char == '}':
				open_el -= 1
				#tmp_str += char
				if (open_el == 0):
					tmp_str = ''
					open_el = -1
			else:
				tmp_str += char
	if open_tags == 0 and open_el == -1:
	process_text(tmp_str)			

def sanitizeData(data):
	sanitizedData = removeTag("br", data)
	for d in sanitizedData:
		print '\n'
		print d
	sanitizedData = removeTagContent("<script","</script>", sanitizedData)
	sanitizedData = removeTagContent("<style","</style>", sanitizedData)
	sanitizedData = removeTagContent("<%","%>", sanitizedData)
	sanitizedData = removeTagContent("<!--","-->", sanitizedData)
	print "############################### after comment"
	for d in sanitizedData:
		print '\n'
		print d
	sanitizedData = removeTag("c:", sanitizedData)
	print "############################### after c"
	for d in sanitizedData:
		print '\n'
		print d
	sanitizedData = removeTagContent("<s:message","(?:</<s:message>)|(?:\>)",sanitizedData)
	print "############################### after s"
	for d in sanitizedData:
		print '\n'
		print d
	sanitizedData = replaceAngularTagWithEl(sanitizedData)
	sanitizedData = removeAngularBracketsInAttrs(sanitizedData)
	return sanitizedData

def removeMessageTagContent(data):
	removeData = 0
	tagsToIgnoreStart = "^.*<s:message"
	tagsToIgnoreEnd = ".*(?:</<s:message>)|(?:\>)"
	sanitizedData = []
	for d in data:
		if re.findall(tagsToIgnoreStart, d):
			if not re.findall(tagsToIgnoreEnd,d):
				removeData += 1
		elif re.findall(tagsToIgnoreEnd,d) and removeData != 0:
				removeData -= 1
		elif removeData == 0:
			sanitizedData.append(d)
	return sanitizedData

def removeAngularBracketsInAttrs(data):
	sanitizedData = []
	for d in data:
		result =  re.findall("\"(?!(?:\s*/?>)|(?:\s*<))[^\"]+\"", d)
		for r in result:
			cleanedString = re.sub("<|>","",r)
			d = d.replace(r,cleanedString)
		sanitizedData.append(d)
	return sanitizedData

def replaceAngularTagWithEl(data):
	sanitizedData = []
	for d in data:
		sanitizedData.append(d.replace('\n', '').replace("{{","${").replace("}}","}"))
	return sanitizedData

def removeTag(tag, data):
	sanitizedData = []
	for d in data:
		sanitizedData.append(re.sub("(?:<"+tag+"\w*[^>]+>?)|(?:</"+tag+"\w*>)","", d))
	return sanitizedData


def removeTagContent(tagStartRegex, tagEndRegex ,data):
	removeData = 0
	tagsToIgnoreStart = "^.*"+tagStartRegex
	tagsToIgnoreEnd = ".*"+tagEndRegex
	sanitizedData = []
	for d in data:
		if re.findall(tagsToIgnoreStart, d):
			if not re.findall(tagsToIgnoreEnd,d):
				removeData += 1
		elif re.findall(tagsToIgnoreEnd,d) and removeData != 0:
			removeData -= 1
		elif removeData == 0:
			sanitizedData.append(d)
	return sanitizedData

def postSanitizeData(d):
	d = d.replace('\n', '').replace("{{","${").replace("}}","}")
	result =  re.sub("(?:<(?:c|s):\w+[^>]+)|(</(?:c|s):\w+>)","", d)
	result =  re.findall("\"(?!(?:\s*/?>)|(?:\s*<))[^\"]+\"", result)
	for r in result:
		cleanedString = re.sub("<|>","",r)
		d = d.replace(r,cleanedString)
	return d
 
# process a file
def process_file(path):
	global current_file_path, open_tags, open_el, removeData
	open_tags = 0
	open_el = -1
	removeData = 0
	current_file_path = path
	with open(path) as f:
		data = sanitizeData(f.readlines())
		#print "final data ",data
		for l in data:
			process_line(l)
 
# process a directory
def process_dir(path):
	for dirpath, dirnames, filenames in os.walk(path):
		for fname in filenames:
			fext = os.path.splitext(fname)[1]
			if fext != '' and fext in FILE_EXTENSIONS.split(','):
				fpath = os.path.join(dirpath, fname)
				process_file(fpath)
 
def process_path(path):
	if os.path.exists(path):
		if(os.path.isdir(path)):
			process_dir(path)
		else:
			process_file(path)

def print_file_path_static_text_map():
	global file_path_static_text_map
	table_str = ""
	for file_name, static_text_arr in file_path_static_text_map.iteritems():
		table_str += "<tr>"
		table_str += "<td rowspan='"+str(len(static_text_arr))+"'>" + file_name + "</td>"
		for i, static_text in enumerate(static_text_arr):
			static_text_col = "<td>"+static_text+"</td>"
			if i == 0:
				table_str += static_text_col
			else:
				table_str += "<tr>"+static_text_col+"</tr>"
		table_str += "</tr>"
	html_str = "<html><head><style>table, th, td {border: 1px solid black;}</style></head><body><table>"+table_str+"</table></body></html>"
	f = open("output.html","w")
	f.write(html_str)
	f.close();
 
# main
##################################################
import sys, os, re
 
current_file_path = ''
file_path_static_text_map = {}
open_tags = 0
open_el = -1
removeData = 0
 
for path in sys.argv[1:]:
	process_path(path)

print_file_path_static_text_map()

# d = "<th class=\"showToolTip\" data-html=\"true\" data-original-title=\"<s:message code='lable.my.application.application.status.date.tooltip' text='Various application status. Draft: You have initiated the enrollment application but not yet completed.
# Submitted: You have submitted and completed the enrollment application.
# Cancelled: You have cancelled your enrollment.
# Expired: You enrollment has expired.'/>\"><s:message code=\"individual.enrollment.application.status\" text=\"Application Status\" /></th>"
# tag = "s:"
# result =  re.sub("(?:<"+tag+"\w*[^>]+>?)|(?:</"+tag+"\w*>)","", d)
# print result



