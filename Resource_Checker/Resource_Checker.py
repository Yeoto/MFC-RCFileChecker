import os, sys
import io
import datetime
from operator import eq
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
RESOURCE_DATA = {'CONTROL'       : 2,
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

print(sys.argv)
realpath = ''
try:
    realpath = os.path.dirname(os.path.abspath(__file__))
except:
    realpath = os.path.dirname(os.path.abspath(sys.argv[0]))

if os.path.exists('./log') == False:
    os.mkdir('./log')

logFileName = realpath + '\\log\\'+datetime.datetime.now().strftime('%y%m%d_%H%M%S')+'log.log'
fLog = io.open(logFileName, mode='w', encoding='utf-16')

# { 'folder' : { 'region(filename)' : { 'dialogname' : { 'control' : 0 } } } }
Loaded_Datas = { }

StrLib.SetLogFile(fLog)
bSendMail = False

CheckFileDatas = []
to_mail = []
#-------------------- 명령인자 처리 --------------------#
SysArgv = sys.argv
del SysArgv[0]

bCheckAllDlg = False

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

#-------------------- 깨짐, 중복 체크 --------------------#
for FolderData in CheckFileDatas:
    Option = FolderData.Option
    FileLib.SetOption(Option)
    FileLib.SetLogger(fLog)
    PathList = FolderData.RCFilePaths

    for rcfilepath in PathList:
        filename = rcfilepath.FileFullPath
        author = rcfilepath.Author
        rev = rcfilepath.Revision
        bFind = False
        nline = 0

        decoding_type = MyUtility.GetEncoding(rcfilepath.FileFullPath)

        StrLib.SetDecodingType(decoding_type)
        folderName = PathLib.GetUpperDirectoryName(filename)
        if not folderName in Loaded_Datas:
            Loaded_Datas[folderName] = {}

        if not os.path.isfile(filename):
            StrLib.print_new('Not Exist File ! : ' + filename)

        FilenameOnly = os.path.basename(filename)
        if not FilenameOnly in Loaded_Datas:
            Loaded_Datas[folderName][FilenameOnly] = {}

        StrLib.print_new('Checking File... : %s' % (filename))

        rc_file = io.open(filename, 'rb')

        rc_file.seek(0)
        rc_lines = FileLib.ReadLines(rc_file, decoding_type)

        CheckDlgList = []
        tmpFilePath = PathLib.GetUpperDirectoryPath(filename)
        tmpFileName, tmpFileExt = os.path.basename(filename).split('.')
        tmpFileName = tmpFileName + "_tmp"
        tmpFilePath = tmpFilePath + tmpFileName + '.' + tmpFileExt
        if os.path.isfile(tmpFilePath):
            rc_tmpfile = io.open(tmpFilePath, 'r', decoding_type)
            CheckDlgList = FileLib.MakeDataForDiffbyFile(rc_tmpfile, rc_file)
            bCheckAllDlg = False
            rc_tmpfile.close()
        else:
            bCheckAllDlg = True

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
                bContinue = False
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
                               StrLib.print_new("%d : %s, Can't Check Dialog With #if #endif" % (nline-i-1, strDialogIDD))
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

            if rc_datas[0] in RESOURCE_DATA:
                if bInDialog == False:
                    continue
                try:
                    place = RESOURCE_DATA[rc_datas[0]]
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
                        except BaseException:
                            str = "Broken in %s. %d : Can't Print out Text" % (strDialogIDD, nline)
                            StrLib.print_new(str)
                    else:
                        bPrintOverlap = ValueLib.IsPrintOverlap(rc_datas[0], Option.bNoOverlap)
                        if Option.bNoOverlap==True and resource_ID.find('IDC_STATIC') >= 0:
                            bPrintOverlap = False

                        if bPrintOverlap and resource_ID in used_rID:
                            bFind = True
                            try:
                                str = "Overlap in %s. %d : %s" % (strDialogIDD, nline ,rc_line)
                                StrLib.print_new("Overlap in %s. %d : %s" % (strDialogIDD, nline ,rc_line))
                            except BaseException:
                                str = "Overlap in %s. %d : Can't Print out Text" % (strDialogIDD, nline)
                                StrLib.print_new(str)
                        else:
                            used_rID[resource_ID] = 1;
                except BaseException:
                    if Option.bNoPirntExcept == False:
                        ttt = ", ".join(rc_datas)
                        str = 'EXCEPTION !! ' + str(nline) + ' : ' + ttt
                        StrLib.print_new(str)
            else:
                bAttach = False
                prev_needLen = 0

        if bFind == True:
            bSendMail = True
            StrLib.print_new('\n\n\n')
            if Option.bNoEmail == False:
                to_mail.append(author)

        rc_file.close()
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

if bSendMail == True and Option.bNoEmail == False:
    eMailInst = emaillib.emaillib()
    eMailInst.sendMail(to_mail,[logFileName])

StrLib.SetDecodingType('utf-8')
StrLib.print_new(u"Resource Checker Successfully Complete !")

fLog.close()