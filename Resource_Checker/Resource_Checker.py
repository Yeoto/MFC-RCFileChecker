#-*- coding: utf-8 -*-
import os, sys
import codecs
import datetime
import time
import re
from operator import eq
from junit_xml import TestSuite, TestCase
import emaillib
import MyUtility

class RCFilePath():
    def __init__(self):
        self.FileName = ''
        self.FileFullPath = ''
        self.Revision = 0
        self.Author = ''

    def SetRCPath(self, FileFullPath, Revision, Author):
        self.FileFullPath = FileFullPath
        self.FileName = os.path.basename(FileFullPath)
        self.Revision = Revision
        self.Author = Author

class RCFolderData():
    def __init__(self):
        self.Option = MyUtility.OptionData()
        self.RCFilePaths = []

decoding_type = 'utf-8'
resource_data = {'CONTROL'       : 2,
                 'PUSHBUTTON'    : 2,
                 'GROUPBOX'      : 2,
                 'COMBOBOX'      : 1,
                 'EDITTEXT'      : 1,
                 'DEFPUSHBUTTON' : 2,
                 'LTEXT'         : 2,
                 'RTEXT'         : 2,
                 'LISTBOX'       : 1,
                 'CTEXT'         : 2}

StrLib = MyUtility.StringLib()
PathLib = MyUtility.PathLib()
ValueLib = MyUtility.ValueLib()
FileLib = MyUtility.FileLib()

now_time = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
strToday = datetime.datetime.now().strftime('%Y-%m-%d')

strYesterDay = ''

if datetime.datetime.today().weekday() == 0:
    strYesterDay = (datetime.datetime.now()-datetime.timedelta(3)).strftime('%Y-%m-%d')
else:
    strYesterDay = (datetime.datetime.now()-datetime.timedelta(1)).strftime('%Y-%m-%d')

print(sys.argv)
realpath = ''
try:
    realpath = os.path.dirname(os.path.abspath(__file__))
except:
    realpath = os.path.dirname(os.path.abspath(sys.argv[0]))

if os.path.exists('./log') == False:
    os.mkdir('./log')

logFileName = realpath + '\\log\\'+now_time+'log.log'
fLog = codecs.open(logFileName, 'a+', 'utf-16')

# { 'folder' : { 'region(filename)' : { 'dialogname' : { 'control' : 0 } } } }
Loaded_Datas = { }

StrLib.SetLogFile(fLog)
bSendMail = False

CheckFileDatas = []
to_mail = []
#-------------------- 명령인자 처리 --------------------#
SysArgv = sys.argv
del SysArgv[0]
nMode = 0
if len(SysArgv) == 0:
    nMode = 1
elif len(SysArgv) >= 1:
    if eq(SysArgv[0], 'AfterBuild'):
        nMode = 1
    elif eq(SysArgv[0], 'AfterCommit'):
        nMode = 2
    elif eq(SysArgv[0], 'Daily'):
        nMode = 3

bCheckAllDlg = False
if nMode == 1:
    f = open(realpath + '\\Source_Repo.txt', 'r')
    buildmode_lines = f.readlines()
    for BuildModeLine in buildmode_lines:
        if not BuildModeLine: break

        BuildModeLine = BuildModeLine.strip()
        if not BuildModeLine: continue
        
        if eq(BuildModeLine[0], '#'): continue

        FolderData = RCFolderData()

        export_datas = StrLib.parser(BuildModeLine)
        FolderData.Option.SetOption(export_datas)

        FolderData.RCFilePaths = PathLib.GetRCFileList(export_datas[0])

        CheckFileDatas.append(FolderData)
        bCheckAllDlg = True
    f.close()
elif nMode == 2:
    nData = 0

    FolderData = RCFolderData()
    FolderData.Option.SetOptionForCommit()
    FolderData.Option.SetOption(sys.argv)
    File_List = []
    File_List_Sorted = []

    File_List.extend(PathLib.GetRCFileList(SysArgv[1]))
    File_List_Sorted = list(set(File_List))
    File_List_Sorted.sort()

    for strFilePath in File_List_Sorted:
        FilePath = RCFilePath()
        FilePath.SetRCPath(strFilePath, 0, "")
        FolderData.RCFilePaths.append(FilePath)
    CheckFileDatas.append(FolderData)
    bCheckAllDlg = False
elif nMode == 3:
    from xml.etree.ElementTree import XML, fromstring, tostring
    import subprocess
    print('Updating Source...'),
    str_update = subprocess.Popen("\"C:\\Program Files\\TortoiseSVN\\bin\\svn.exe\" update " + SysArgv[1], stdout=subprocess.PIPE).stdout.read()
    print('Done !')
    str_xml = subprocess.Popen("\"C:\\Program Files\\TortoiseSVN\\bin\\svn.exe\" log "+ SysArgv[1] + " --xml -v -r {" + strYesterDay + "}:HEAD", stdout=subprocess.PIPE).stdout.read()
    elem = XML(str_xml)

    FolderData = RCFolderData()
    FolderData.Option.SetOptionForDaily()
    File_List = []
    File_rev_List = {}
    for logentry in elem.findall('logentry'):
        bFindRC = False
        path_str = ''
        for paths in logentry.findall('paths'):
            for path in paths.findall('path'):
                regex = re.compile(r"(.+)\.rc")
                result = regex.findall(path.text)
                if len(result) >= 1:
                    path_str = path.text.replace('/',"\\")
                    regex2 = re.compile(r"(\\[\w|\d|\.]+)")
                    result2 = regex2.findall(path_str)
                    path_str = SysArgv[1] + ''.join(result2[2:])
                    File_List.append(path_str)
                    if not File_rev_List.has_key(path_str):
                        File_rev_List[path_str] = []
                    if not (logentry.attrib['revision'], logentry.find('author').text) in File_rev_List[path_str]:
                        File_rev_List[path_str].append((logentry.attrib['revision'], logentry.find('author').text))
                    bFindRC = True

    File_list_Sorted = list(set(File_List))
    File_list_Sorted.sort()
    for strFilePath in File_list_Sorted:
        if File_rev_List.has_key(strFilePath):
            for (rev,author) in File_rev_List[strFilePath]:
                FilePath = RCFilePath()
                FilePath.SetRCPath(strFilePath, int(rev), author)
                FolderData.RCFilePaths.append(FilePath)
    CheckFileDatas.append(FolderData)
    bCheckAllDlg = True
    #to_mail = 

#-------------------- 명령인자 처리 --------------------#

#-------------------- 깨짐, 중복 체크 --------------------#
test_cases = []
for FolderData in CheckFileDatas:
    Option = FolderData.Option
    FileLib.SetOption(Option)
    FileLib.SetLogger(fLog)
    PathList = FolderData.RCFilePaths
    bExportXml = Option.bExportXML

    for rcfilepath in PathList:
        filename = rcfilepath.FileFullPath
        author = rcfilepath.Author
        rev = rcfilepath.Revision
        bFind = False
        nline = 0

        test_case = TestCase(filename)

        #kr, ch, long만 체크할꺼임..
        if filename.find('_ch') > 0:
            decoding_type = 'gbk'
        elif filename.find('_rus') > 0:
            if Option.bNoRussia == False:
                decoding_type = 'cp1251'
            else:
                test_case.add_skipped_info('CAN NOT Encode This File');
                test_cases.append(test_case)
                continue
        elif filename.find('_jp') > 0:
            continue
        elif filename.find('_long') > 0:
            decoding_type = 'euc-kr'
        else:
            decoding_type = 'euc-kr'

        test_case.allow_multiple_subalements = True;

        StrLib.SetDecodingType(decoding_type)
        folderName = PathLib.GetUpperDirectoryName(filename)
        if not folderName in Loaded_Datas:
            Loaded_Datas[folderName] = {}

        if not os.path.isfile(filename):
            StrLib.print_new('Not Exist File ! : ' + filename)

        FilenameOnly = os.path.basename(filename)
        if not FilenameOnly in Loaded_Datas:
            Loaded_Datas[folderName][FilenameOnly] = {}

        if nMode == 3:
            StrLib.print_new('Checking File... : %s:%d by %s' % (filename, rev, author))
        elif nMode == 2:
            StrLib.print_new('Checking File... : %s' % (filename))

        rc_file = codecs.open(filename, 'rb')

        rc_file.seek(0)
        rc_lines = FileLib.ReadLines(rc_file, decoding_type)

        CheckDlgList = []
        if nMode == 2:
            tmpFilePath = PathLib.GetUpperDirectoryPath(filename)
            tmpFileName, tmpFileExt = os.path.basename(filename).split('.')
            tmpFileName = tmpFileName + "_tmp"
            tmpFilePath = tmpFilePath + tmpFileName + '.' + tmpFileExt
            if os.path.isfile(tmpFilePath):
                rc_tmpfile = codecs.open(tmpFilePath, 'r', decoding_type)
                CheckDlgList = FileLib.MakeDataForDiffbyFile(rc_tmpfile, rc_file)
                bCheckAllDlg = False
                rc_tmpfile.close()
            else:
                bCheckAllDlg = True
        elif nMode == 3:
            early_rev = subprocess.Popen("\"C:\\Program Files\\TortoiseSVN\\bin\\svn.exe\" cat "+ filename + " -r " + str(rev-1), stdout=subprocess.PIPE).stdout.read()

            early_rev = early_rev.replace('\r\n', '\n')
            p = re.compile(r".*\n")
            early_rev_lines = p.findall(early_rev)

            prev_rev_lines = []
            for early_line in early_rev_lines:
                (bSuccess, early_line_temp) = StrLib.CheckAllEncode(early_line, decoding_type)
                
                if bSuccess:
                    prev_rev_lines.append(early_line_temp)
                else:
                    prev_rev_lines.append(early_line)

            print('Diff Previous Revision...'),
            CheckDlgList = FileLib.MakeDataForDiffbyStr(filename+'tmp',prev_rev_lines,filename+'org', rc_lines)
            print('Done!')
            bCheckAllDlg = False

        bInDialog = False
        prev_line = ''
        prev_needLen = 0
        bAttach = False
        bStartDialog = False
        control_counter = {}
        used_rID = {}
        strDialogIDD = ''
        
        bCount = True
        for current_line in rc_lines:
            nline = nline+1
            try:
                if bAttach == True:
                    rc_line = prev_line + current_line
                else:
                    rc_line = current_line
            except BaseException:
                rc_line = ''
                continue

            #처음부터 아무것도 없으면 파일 끝
            if not rc_line: break
            rc_line = rc_line.strip()

            #strip 하고 아무것도 없으면 \n나 ' '사라진것
            if not rc_line: continue
            rc_datas = StrLib.parser(rc_line)

            if bAttach == True and len(rc_datas) <= prev_needLen:
                rc_line = current_line
                rc_datas = StrLib.parser(rc_line)

            if rc_line == '// Dialog':
                bStartDialog = True
                continue

            if bStartDialog == False:
                continue

            if 'STYLE' in rc_datas:
                used_rID.clear()
                bContinue = False;
                bPrintError = True
                for i in range(1,10): #10줄 검사
                    past_Data = StrLib.parser(rc_lines[nline-i-1].strip())
                    if not past_Data: continue
                    if eq(past_Data[0],'END') or eq(rc_lines[nline-i-1].strip(), '// Dialog'):
                        break
                    if past_Data[0].find('#if') >= 0:
                        if (bool(strDialogIDD) == True) and (bPrintError == True):
                            bPrintError = False
                            if Option.bNoWarnIF == False:
                               str = "%d : %s, Can't Check Dialog With #if #endif" % (nline-i-1, strDialogIDD)
                               StrLib.print_new(str)
                               test_case.add_skipped_info(str)
                        bContinue = True
                    elif len(past_Data) >= 6:
                        if past_Data[1].find('DIALOG') >= 0:
                            if bCheckAllDlg == False:
                                if not past_Data[0] in CheckDlgList:
                                    bContinue = True
                            strDialogIDD = past_Data[0]
                            bInDialog = True

                if bContinue == True: 
                    bInDialog = False
                    strDialogIDD = ''
                    continue

                if strDialogIDD not in Loaded_Datas[folderName][FilenameOnly]:
                    Loaded_Datas[folderName][FilenameOnly][strDialogIDD] = {}
                    bCount = True
                else:
                    StrLib.print_new("%d : %s Dialog is Overlapped. It will count based first one." % (nline,strDialogIDD))
                    bCount = False            

            if eq(rc_line, 'END'):
                bInDialog = False
                continue

            if rc_datas[0] in resource_data:
                if bInDialog == False:
                    continue
                try:
                    place = resource_data[rc_datas[0]]
                    if len(rc_datas) <= place:
                        prev_line = rc_line
                        prev_needLen = place
                        bAttach = True
                        continue

                    if bCount == True:
                        if rc_datas[0] not in Loaded_Datas[folderName][FilenameOnly][strDialogIDD]:
                            Loaded_Datas[folderName][FilenameOnly][strDialogIDD][rc_datas[0]] = 0
                        Loaded_Datas[folderName][FilenameOnly][strDialogIDD][rc_datas[0]] += 1;

                    bAttach = False
                    prev_needLen = 0

                    resource_ID = rc_datas[place]

                    if ValueLib.IsDigit(resource_ID):
                        bFind = True
                        try:
                            str = 'Broken in %s. %d : %s' % (strDialogIDD, nline, rc_line)
                            StrLib.print_new(str)
                            test_case.add_error_info(str,None,'BROKEN_IDD')
                        except BaseException:
                            str = "Broken in %s. %d : Can't Print out Text" % (strDialogIDD, nline)
                            StrLib.print_new(str)
                            test_case.add_failure_info(str,None,"ENCODE_ERR")
                    else:
                        bPrintOverlap = ValueLib.IsPrintOverlap(rc_datas[0], Option.bNoOverlap)
                        if Option.bNoOverlap==True and resource_ID.find('IDC_STATIC') >= 0:
                            bPrintOverlap = False

                        if bPrintOverlap and resource_ID in used_rID:
                            bFind = True
                            try:
                                str = "Overlap in %s. %d : %s" % (strDialogIDD, nline ,rc_line)
                                StrLib.print_new("Overlap in %s. %d : %s" % (strDialogIDD, nline ,rc_line))
                                test_case.add_error_info(str,None,'OVERLAP_IDD')
                            except BaseException:
                                str = "Overlap in %s. %d : Can't Print out Text" % (strDialogIDD, nline)
                                StrLib.print_new(str)
                                test_case.add_failure_info(str,None,"ENCODE_ERR")
                        else:
                            used_rID[resource_ID] = 1;
                except BaseException:
                    if Option.bNoPirntExcept == False:
                        ttt = ", ".join(rc_datas)
                        str = 'EXCEPTION !! ' + str(nline) + ' : ' + ttt
                        StrLib.print_new(str)
                        test_case.add_failure_info(str,None,"EXCEPTION")
            else:
                bAttach = False
                prev_needLen = 0

        if bFind == True:
            bSendMail = True
            StrLib.print_new('\n\n\n')
            if Option.bNoEmail == False:
                to_mail.append(author)

        rc_file.close()
        if bExportXml == True:
            test_cases.append(test_case)
#-------------------- 깨짐, 중복 체크 --------------------#

#-------------------- 대화상자 별 컨트롤 갯수 체크 --------------------#
if Option.bNoRagionChk == False:
    StrLib.print_new("Start Checking each region...")

    for FolderKey in Loaded_Datas.keys():
        Folder = Loaded_Datas[FolderKey]
        RegionList = list(Folder.keys())

        if bool(RegionList) == False:
            StrLib.print_new("Can't Find Resource Files in %s or No Dialog Data." % FolderKey)

        #뒤에 아무것도 안붙는 녀석이 가장 앞에 와야함.
        RegionList.sort()

        if RegionList[0].find('_ch') >= 0 and RegionList[0].find('_rus') >= 0 and RegionList[0].find('_jp') >= 0 and RegionList[0].find('_long') >= 0:
            StrLib.print_new("Can't Find KR Resource Files in %s." % FolderKey)

        KRResource = Folder[RegionList[0]]

        for strRegion in RegionList:
            for KRData in list(KRResource.keys()):
                if not Folder[strRegion].has_key(KRData):
                    bSendMail = True
                    StrLib.print_new("Error : %s Resource File doesn't include Dialog %s" % (strRegion, KRData))
                elif Folder[strRegion][KRData] != KRResource[KRData]:
                    bSendMail = True
                    StrLib.print_new("Error : %s Dialog's Controls don't correct each other %s" % (strRegion, KRData))
#-------------------- 대화상자 별 컨트롤 갯수 체크 --------------------#

fLog.flush()

if len(test_cases) > 0:
    ts = TestSuite("Resource Checker", test_cases)
    with open(Option.XmlOutput, 'w') as fXml:
        TestSuite.to_file(fXml, [ts], prettyprint=False)

if bSendMail == True and Option.bNoEmail == False:
    eMailInst = emaillib.emaillib()
    eMailInst.sendMail(to_mail,[logFileName])

StrLib.SetDecodingType('utf-8')
StrLib.print_new(u"Resource Checker Successfully Complete !")

fLog.close()