#!/usr/bin/python


from HTMLParser import HTMLParser

# constants
##################################################
FILE_EXTENSIONS = '.jsp,'


class MyHTMLParser(HTMLParser):

    text = []
    current_tag = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        #print "tag",tag
        for attr in attrs:
            if (attr[0] == "title" or attr[0] == "alt"):
                if not "<s:message" in attr[1]: self.text.append(attr[1])
    def handle_endtag(self, tag):
        self.current_tag = ''
    def handle_data(self, data):
        if self.current_tag != 'script' and self.current_tag != 'style':
            data_strip = data.strip()
            if data_strip: 
                #print "data_strip", data_strip
                self.text.append(data_strip)
    def get_text(self):
        return self.text

def sanitizeData(data):
    global current_file_path
    stripped_text = reduce_data(data)
    sanitizedData = removeTagContent("<%--","--%>", stripped_text)
    sanitizedData = removeJSPDirectiveContent(sanitizedData)
    sanitizedData = removeTag("br", sanitizedData)
    sanitizedData = removeTag("stron", sanitizedData)
    sanitizedData = removeMessageTagContent(sanitizedData)
    sanitizedData = replaceAngularTagWithEl(sanitizedData)
    sanitizedData = removeCharacterEntityReference(sanitizedData)
    sanitizedData = removeTag("c:if", sanitizedData)
    #createTmpFile(sanitizedData, current_file_path+'_sanitized')
    return sanitizedData

def reduce_data(data):
    output_str = ''
    for d in data:
        output_str = output_str + d.strip()
    return output_str

def removeJSPDirectiveContent(data):
    sanitizedData = []
    for d in data:
        sanitizedData.append(re.sub("(?:<%@[^%]+%>)","", d))
    return sanitizedData

def removeTag(tag, data):
    sanitizedData = []
    for d in data:
        sanitizedData.append(re.sub("(?:<"+tag+"\w*[^>]+>?)|(?:</"+tag+"\w*>)","", d))
    return sanitizedData

def sanitizeFile(path):
    with open(path) as f:
        data = sanitizeData(f.readlines())
        createTmpFile(data, path)

def createTmpFile(data, path):
    tmp_path = path + ".tmp"
    f_out = open(tmp_path, "w")
    for d in data:
        f_out.write(d)
    f_out.close()

def removeCharacterEntityReference(data):
    characterEntityReferenceArr = ["&lt;", "&gt;"]
    sanitizedData = []
    for d in data:
        sanitizedData.append(re.sub("(&lt;)|(&gt;)","", d))
    return sanitizedData

def replaceAngularTagWithEl(data):
    sanitizedData = []
    for d in data:
        sanitizedData.append(d.replace('\n', '').replace("{{","${").replace("}}","}"))
    return sanitizedData

def removeTagContent(tagStartRegex, tagEndRegex ,data):
    removeData = 0
    tagsToIgnoreStart = "^.*"+tagStartRegex
    tagsToIgnoreEnd = ".*"+tagEndRegex
    sanitizedData = []
    for d in data:
        if re.findall(tagsToIgnoreStart, d):
            if not re.findall(tagsToIgnoreEnd,d): removeData += 1
        elif re.findall(tagsToIgnoreEnd,d) and removeData != 0: removeData -= 1
        elif removeData == 0: sanitizedData.append(d)
    return sanitizedData

def removeMessageTagContent(data):
    messageTagStarted = False
    messageTagStart = "<s:message[^>]+(?<!/)>?"
    messageTagEnd = "(?:</s:message>)|(?:/>)"
    sanitizedData = []
    for d in data:
        if re.findall(messageTagStart, d):
            messageTagStarted = True
            d = re.sub(messageTagStart,'',d)
            if re.findall(messageTagEnd, d):
                d = re.sub(messageTagEnd, '', d)
                messageTagStarted = False
            sanitizedData.append(d)
        elif messageTagStarted:
            if re.findall(messageTagEnd, d):
                sanitizedData.append(re.sub(messageTagEnd,'',d))
                messageTagStarted = False
        else:
            sanitizedData.append(d)
    return sanitizedData

# process plain text
def process_text(text):
    global current_file_path, file_path_static_text_map
    text_strip = text.strip()
    if text_strip:
        file_path_static_text_map.setdefault(current_file_path, [])
        file_path_static_text_map[current_file_path].append(text)
    return text

# process a line
def process_line(l):
    str_parts = []
    open_tags = 0
    open_el = -1
    tmp_str=''
    for i, char in enumerate(l):
        if open_el == -1:
            if char == '$':
                if i+1 < len(l) and l[i+1] == '{':
                    if open_tags == 0:
                        tmp_str = process_text(tmp_str)
                    str_parts.append(tmp_str)
                    tmp_str = ''
                    open_el = 0
                tmp_str += char
            elif char == '<':
                if open_tags == 0:
                    tmp_str = process_text(tmp_str)
                    str_parts.append(tmp_str)
                    tmp_str = ''
                tmp_str += char
                open_tags += 1
            elif char == '>':
                tmp_str += char
                open_tags -= 1
                if open_tags == 0:
                    str_parts.append(tmp_str)
                    tmp_str = ''
            else:
                tmp_str += char
        else:
            if char == '{':
                open_el += 1
                tmp_str += char
            elif char == '}':
                open_el -= 1
                tmp_str += char
                if (open_el == 0):
                    str_parts.append(tmp_str)
                    tmp_str = ''
                    open_el = -1
            else:
                tmp_str += char
    tmp_str = process_text(tmp_str)         
    str_parts.append(tmp_str)
 
    return "".join(str_parts)

# process a file
def process_file(path):
    global current_file_path
    current_file_path = path
    sanitizeFile(path)
    # parser = MyHTMLParser()
    # parser.feed(open(path+'.tmp').read())
    # #print "parser.text",parser.text
    # for l in parser.text:
    #     process_line(l)
    # del parser.text[:]
    # os.remove(path+'.tmp')

 
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
    #print file_path_static_text_map
    table_str = ""
    for file_name, static_text_arr in file_path_static_text_map.iteritems():
        table_str += "<tr>"
        print "filename" , file_name
        table_str += "<td rowspan='"+str(len(static_text_arr))+"'>" + file_name + "</td>"
        for i, static_text in enumerate(static_text_arr):
            print "staticText", static_text
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
 
#properties = {}
current_file_path = ''
file_path_static_text_map = {}
 
for path in sys.argv[1:]:
    process_path(path)

print_file_path_static_text_map()

# messageTagStart = "<s:message[^>]+>?"
# messageTagEnd = "(?:</s:message>)|(?:\\\>)"
# d = "<h1><s:message code=\"exchange.brokers.label.heading\"\></h1>"
# d = re.sub(messageTagStart,'',d)
# print re.sub(messageTagEnd,'',d)
