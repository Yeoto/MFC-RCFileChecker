import glob
import re
from operator import eq
import datetime

class OptionData:
    def __init__(self):
        self.bNoPirntExcept = False
        self.bNoOverlap = False
        self.bNoRussia = False
        self.bNoWarnIF = False
        self.bNoEmail = False
        self.bNoRagionChk = False
        self.bExportXML = False
        self.XmlOutput = "junit.xml"

    def SetOption(self, data_list):
        if '/NoExcept' in data_list:
            self.bNoPirntExcept = True
        if '/NoOverlap' in data_list:
            self.bNoOverlap = True
        if '/NoRussia' in data_list:
            self.bNoRussia = True
        if '/NoWarn#if' in data_list:
            self.bNoWarnIF = True
        if '/NoEmail' in data_list:
            self.bNoEmail = True
        if '/NoRegionChk' in data_list:
            self.bNoRagionChk = True
        if '/ExportXml' in data_list:
            self.bExportXML = True
        
        p = re.compile(r"/Output:([\w| |_|-]*)")
        newlist = list(filter(p.match, data_list))
        if len(newlist) >= 1:
            self.XmlOutput = p.match(newlist[0]).group(1)
            self.XmlOutput += '.xml'

    def SetOptionForCommit(self):
        self.bNoPirntExcept = False
        self.bNoOverlap = False
        self.bNoRussia = True
        self.bNoWarnIF = True
        self.bNoEmail = True
        self.bNoRagionChk = True
        self.bExportXML = False
        self.XmlOutput = "junit.xml"

    def SetOptionForDaily(self):
        self.bNoPirntExcept = False
        self.bNoOverlap = False
        self.bNoRussia = True
        self.bNoWarnIF = True
        self.bNoEmail = False
        self.bNoRagionChk = True
        self.bExportXML = False
        self.XmlOutput = "junit.xml"

class PathLib:
    def GetUpperDirectoryName(self, str):
        p = re.compile(r"(\w+(?=\\))+")
        result = p.findall(str)
        return result[-1]

    def GetUpperDirectoryPath(self, str):
        p = re.compile(r"^(.*[\\\/])")
        result = p.findall(str)
        return result[0]

    def GetRCFileList(self, path):
        list = glob.glob(path+'\\*.rc')
        list += glob.glob(path+'\\**\\*.rc')
        return list

class StringLib:
    def __init__(self):
        self.fLog = None
        self.decoding_type = 'utf-16'

    def SetLogFile(self, file):
        self.fLog = file
    def SetDecodingType(self, type):
        self.decoding_type = type

    def parser(self, string):
        parsed = []
        temp = ''
        bParse = False
        for character in string:
            if eq(character,'"'):
                bParse = bParse == False
            if bParse == False and (eq(character,' ') or eq(character,',')):
                if temp:
                    parsed.insert(len(parsed),temp)
                    temp = ''
            else:
                temp = temp + character

        if temp:
            parsed.insert(len(parsed),temp)

        return parsed

    def print_new(self, *args):
        for s in args:
            if type(s) == type('') or type(s) == type(u''):
                try:
                    print(str(s).decode(self.decoding_type).encode('utf-8'))
                except:
                    print(s)

                s = s.replace('\n','\r\n')
                try:
                    self.fLog.write(str(s).decode(self.decoding_type).encode('utf-16'));
                except:
                    self.fLog.write(s);
                self.fLog.write('\r\n')

    def CheckAllEncode(self, str, encode):
        bSuccess = False
        line_temp = ''
        try:
            line_temp = str.decode(encode)
            bSuccess = True
        except BaseException:
            decoding_list = ['cp949', 'chinese', 'cp936', 'cp1251', 'euckr', 'utf-8', 'utf-16']

            bSuccess = False
            line_temp = ''
            for temp_decoding in decoding_list:
                try:
                    line_temp = str.decode(temp_decoding)
                    bSuccess = True
                    break
                except BaseException:
                    bSuccess = False
        return (bSuccess, line_temp)

class ValueLib:
    def IsPrintOverlap(self, rcType, bNoOverlap):
        bPrintOverlap = False
        if eq(rcType,'GROUPBOX'):
            bPrintOverlap = not bNoOverlap
        elif eq(rcType,'LTEXT'):
            bPrintOverlap = not bNoOverlap
        elif eq(rcType,'RTEXT'):
            bPrintOverlap = not bNoOverlap
        else:
            bPrintOverlap = True
        return bPrintOverlap

    def IsDigit(self, str):
        try:
            tmp = float(str)
            return True
        except:
            return False

class FileLib:
    def __init__(self):
        self.StrLib = StringLib()
        self.Option = OptionData()

    def SetOption(self, opt):
        self.Option = opt

    def SetLogger(self, logger):
        self.StrLib.SetLogFile(logger)

    def ReadLines(self, file, decoding_type):
        lines = []
        file.seek(0)
        self.StrLib.SetDecodingType(decoding_type)
        while True:
            line = file.readline()
            if not line: break

            (bSuccess, line_temp) = self.StrLib.CheckAllEncode(line, decoding_type)

            if bSuccess == False:
                self.StrLib.SetDecodingType('utf-8')
                self.StrLib.print_new("EXCEPTION !! Can't Read Text File.")
                self.StrLib.SetDecodingType(decoding_type)
            else:
                lines.append(line_temp)

        return lines

    def MakeDataForDiffbyFile(self, file1, file2):
        return MakeDataForDiffbyStr(self, file1.name, ReadLines(file1), file2.name, ReadLines(file2))

    def MakeDataForDiffbyStr(self, file1_name, file1_line, file2_name, file2_line):
        dialog_list = []
        file_lines_dic = {}
        file_lines_dic[file1_name] = file1_line
        file_lines_dic[file2_name] = file2_line

        dont_CheckDlg = {}

        for file_key, file_lines in file_lines_dic.items():
            nline = 0
            bStartDialog = False
            check_list = []
            if file_key == file1_name:
                check_list = file_lines_dic[file2_name]
            elif file_key == file2_name:
                check_list = file_lines_dic[file1_name]

            bCheckOnce = False
            for f_line in file_lines:
                f_line_temp = f_line.strip()
                nline += 1

                if eq(f_line_temp,'END'):
                    bCheckOnce = False

                #한번 걸리면 다음 END까지 체크 안함
                if bCheckOnce == True:
                    continue

                if bStartDialog == False and f_line_temp == '// Dialog':
                    bStartDialog = True
                    continue

                if bStartDialog == False:
                    continue
                else:
                    p = re.compile(r"^\/\/[ ]*(.+)")
                    result = p.findall(f_line_temp)
                    if len(result) == 1:
                        if not eq(result[0], 'Dialog'):
                            bStartDialog = False

                if not f_line in check_list:
                    bContinue = False
                    bInDialog = False
                    strDialogIDD = ""
                    for i in range(0,100):  #컨트롤이 100개가 넘지는 않겠지..??
                        past_Data = self.StrLib.parser(file_lines[nline-i-1].strip())
                        if not past_Data: continue
                        if eq(past_Data[0],'END') or eq(file_lines[nline-i-1].strip(), '// Dialog'):
                            break
                        if past_Data[0].find('#if') >= 0:
                            dont_CheckDlg[strDialogIDD] = True
                            bContinue = True
                        elif len(past_Data) >= 6:
                            if past_Data[1].find('DIALOG') >= 0:
                                if dont_CheckDlg.has_key(past_Data[0]):
                                    bContinue = True
                                else:
                                    strDialogIDD = past_Data[0]
                                    bInDialog = True

                    if bInDialog == True and bool(strDialogIDD) and bContinue==False:
                        if not strDialogIDD in dialog_list:
                            dialog_list.append(strDialogIDD)
                            bCheckOnce = True

        temp_list = [x for x in dialog_list if not dont_CheckDlg.has_key(x)]
        return list(set(temp_list))