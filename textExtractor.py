#!/usr/bin/python


from HTMLParser import HTMLParser

# constants
##################################################
FILE_EXTENSIONS = '.jsp,'
OMMIT_DIRECTORIES = ['depricated','target','exchange-admin-portal']
WHITE_LISTED_CHARACTERS=['*','|','?','.',':','(',')','%','+','-','\'','$','[',']',',',':: ::','!','`']


class MyHTMLParser(HTMLParser):

    text = []
    current_tag = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        for attr in attrs:
            if (attr[0] == "title" or attr[0] == "alt"):self.text.append(attr[1])
    def handle_endtag(self, tag):
        self.current_tag = ''
    def handle_data(self, data):
        if self.current_tag != 'script' and self.current_tag != 'style':
            data_strip = data.strip()
            if data_strip: 
                self.text.append(data_strip)
    def get_text(self):
        return self.text

def sanitizeData(data):
    global current_file_path
    stripped_text = reduce_data(data)
    sanitizedData = removeTagContent("<%--","--%>", stripped_text)
    sanitizedData = removeTagContent("<%@","%>", sanitizedData)
    sanitizedData = removeTagContent("<!--","-->", sanitizedData)
    sanitizedData = removeBreakTag(sanitizedData)
    sanitizedData = removeTag("strong", sanitizedData)
    sanitizedData = removeMessageTagContent(sanitizedData)
    sanitizedData = removeFormatTagContent(sanitizedData)
    sanitizedData = replaceAngularTagWithEl(sanitizedData)
    sanitizedData = removeCharacterEntityReference(sanitizedData)
    sanitizedData = removeTag("c:if", sanitizedData)
    return sanitizedData

def reduce_data(data):
    output_str = ''
    for d in data:
        output_str = output_str + re.sub("\n|\t|\r","", d)
    return output_str

def removeAngularBracketsInAttrs(data):
    result =  re.findall("(?<!>)\"(?!(?:\s*/?>)|(?:\s*<))[^\"]+\"", data)
    for r in result:
        cleanedString = re.sub("<|>","",r)
        data = data.replace(r,cleanedString)
    return data

def removeBreakTag(data):
    brRegex = "(?:<br>)|(?:</br>)|(?:<br/>)"
    return re.sub(brRegex, '', data)

def removeTag(tag, data):
    regex = "(?:<"+tag+".*?>)|(?:</"+tag+">)"
    return re.sub(regex, '', data)

def sanitizeFile(path):
    with open(path) as f:
        data = sanitizeData(f.readlines())
        createTmpFile(data, path)

def createTmpFile(data, path):
    tmp_path = path + ".tmp"
    f_out = open(tmp_path, "w")
    f_out.write(data)
    f_out.close()

def removeCharacterEntityReference(data):
    return re.sub("(&lt;)|(&gt;)","", data)

def replaceAngularTagWithEl(data):
    return data.replace("{{","${").replace("}}","}")

def removeTagContent(tagStartRegex, tagEndRegex ,data):
    regex = tagStartRegex + ".*?" + tagEndRegex
    return re.sub(regex, '', data)

def removeMessageTagContent(data):
    regex = "(?:<s:message.*?/?>)|(?:</s:message>)"
    return re.sub(regex, '', data)

def removeFormatTagContent(data):
    regex = "(?:<fmt:formatDate.*?/?>)|(?:</fmt:formatDate>)"
    return re.sub(regex, '', data)

# process plain text
def process_text(text):
    global current_file_path, file_path_static_text_map
    text_strip = text.strip()
    if text_strip and not white_listed(text_strip):
        file_path_static_text_map.setdefault(current_file_path, [])
        file_path_static_text_map[current_file_path].append(text)
    return text

def white_listed(text):
    return text.find("<") != -1 or text.find(">") != -1 or (text in WHITE_LISTED_CHARACTERS)

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
    parser = MyHTMLParser()
    parser.feed(open(path+'.tmp').read())
    #print parser.text
    for l in parser.text:
        process_line(l)
    del parser.text[:]
    os.remove(path+'.tmp')

 
# process a directory
def process_dir(path):
    for dirpath, dirnames, filenames in os.walk(path):
        if not ommitted_directory(dirpath):
            for fname in filenames:
                fext = os.path.splitext(fname)[1]
                if fext != '' and fext in FILE_EXTENSIONS.split(','):
                    fpath = os.path.join(dirpath, fname)
                    process_file(fpath)

def ommitted_directory(dirpath):
    for ommitted_directory in OMMIT_DIRECTORIES:
        if ommitted_directory in dirpath:
            return True
    return False
 
def process_path(path):
    if os.path.exists(path):
        if(os.path.isdir(path)):
            process_dir(path)
        else:
            process_file(path)

def print_file_path_static_text_map(outputFile='output.html'):
    global file_path_static_text_map
    #print file_path_static_text_map
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
    f = open(outputFile,"w")
    f.write(html_str)
    f.close();
 
# main
##################################################
import sys, os, re
 
#properties = {}
current_file_path = ''
file_path_static_text_map = {}
 
for path in sys.argv[1:-1]:
    process_path(path)

print_file_path_static_text_map(sys.argv[-1])
