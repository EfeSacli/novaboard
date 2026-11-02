Option Explicit

Dim WshShell, fso, strDesktop, strCurrentDir, oShortcut, pyExe
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDesktop = WshShell.SpecialFolders("Desktop")
strCurrentDir = fso.GetParentFolderName(WScript.ScriptFullName)

If Not fso.FileExists(strCurrentDir & "\app.py") Then
    If fso.FileExists(fso.GetParentFolderName(strCurrentDir) & "\app.py") Then
        strCurrentDir = fso.GetParentFolderName(strCurrentDir)
    End If
End If

Function FindSignedPythonW()
    FindSignedPythonW = ""
    Dim candidates, c, localAppData
    localAppData = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    candidates = Array( _
        strCurrentDir & "\runtime\pythonw.exe", _
        localAppData & "\Python\pythoncore-3.14-64\pythonw.exe", _
        localAppData & "\Python\bin\pythonw.exe", _
        localAppData & "\Programs\Python\Python314\pythonw.exe", _
        localAppData & "\Programs\Python\Python313\pythonw.exe", _
        localAppData & "\Programs\Python\Python312\pythonw.exe" _
    )
    For Each c In candidates
        If fso.FileExists(c) Then
            If fso.GetFile(c).Size > 1024 Then
                FindSignedPythonW = c
                Exit Function
            End If
        End If
    Next
End Function

pyExe = FindSignedPythonW()

Set oShortcut = WshShell.CreateShortcut(strDesktop & "\Novaboard.lnk")
If pyExe <> "" Then
    oShortcut.TargetPath = pyExe
    oShortcut.Arguments = """" & strCurrentDir & "\app.py"""
Else
    oShortcut.TargetPath = "wscript.exe"
    oShortcut.Arguments = """" & strCurrentDir & "\Baslat_Windows.vbs"""
End If
oShortcut.WorkingDirectory = strCurrentDir
oShortcut.IconLocation = strCurrentDir & "\icon.ico, 0"
oShortcut.Description = "Novaboard - Akıllı Tahta & Öğretmen Asistanı"
oShortcut.Save

MsgBox "Novaboard masaüstü kısayolu başarıyla oluşturuldu!" & vbCrLf & vbCrLf & "Artık programı doğrudan masaüstünüzdeki simgeden tek tıkla (Akıllı Uygulama Denetimi engeline takılmadan) çalıştırabilirsiniz.", 64, "Novaboard - Kısayol Eklendi"
