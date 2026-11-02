Option Explicit

Dim WshShell, fso, strCurrentDir, appScript
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strCurrentDir = fso.GetParentFolderName(WScript.ScriptFullName)

If fso.FileExists(strCurrentDir & "\app.py") Then
    appScript = strCurrentDir & "\app.py"
    WshShell.CurrentDirectory = strCurrentDir
ElseIf fso.FileExists(fso.GetParentFolderName(strCurrentDir) & "\app.py") Then
    strCurrentDir = fso.GetParentFolderName(strCurrentDir)
    appScript = strCurrentDir & "\app.py"
    WshShell.CurrentDirectory = strCurrentDir
Else
    MsgBox "app.py bulunamadı: " & strCurrentDir, 16, "Novaboard - Başlatma Hatası"
    WScript.Quit 1
End If

Function IsValidPythonExe(exePath)
    IsValidPythonExe = False
    On Error Resume Next
    If exePath <> "" Then
        If InStr(LCase(exePath), "\windowsapps\") = 0 Then
            If fso.FileExists(exePath) Then
                If fso.GetFile(exePath).Size > 1024 Then
                    IsValidPythonExe = True
                End If
            End If
        End If
    End If
    On Error GoTo 0
End Function

Function FindSignedPythonW()
    FindSignedPythonW = ""
    Dim candidates, c, localAppData, progFiles, folder, subFolder

    localAppData = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    progFiles = WshShell.ExpandEnvironmentStrings("%ProgramFiles%")

    ' 1. Paket içi taşınabilir (Microsoft/PSF imzalı) runtime kontrolü
    candidates = Array( _
        strCurrentDir & "\runtime\pythonw.exe", _
        localAppData & "\Python\pythoncore-3.14-64\pythonw.exe", _
        localAppData & "\Python\bin\pythonw.exe", _
        localAppData & "\Programs\Python\Python314\pythonw.exe", _
        localAppData & "\Programs\Python\Python313\pythonw.exe", _
        localAppData & "\Programs\Python\Python312\pythonw.exe", _
        localAppData & "\Programs\Python\Python311\pythonw.exe" _
    )

    For Each c In candidates
        If IsValidPythonExe(c) Then
            FindSignedPythonW = c
            Exit Function
        End If
    Next

    ' 2. %LOCALAPPDATA%\Python altındaki tüm pythoncore-* klasörlerini tara
    If fso.FolderExists(localAppData & "\Python") Then
        Set folder = fso.GetFolder(localAppData & "\Python")
        For Each subFolder In folder.SubFolders
            If IsValidPythonExe(subFolder.Path & "\pythonw.exe") Then
                FindSignedPythonW = subFolder.Path & "\pythonw.exe"
                Exit Function
            End If
        Next
    End If

    ' 3. %LOCALAPPDATA%\Programs\Python altındaki tüm Python* klasörlerini tara
    If fso.FolderExists(localAppData & "\Programs\Python") Then
        Set folder = fso.GetFolder(localAppData & "\Programs\Python")
        For Each subFolder In folder.SubFolders
            If IsValidPythonExe(subFolder.Path & "\pythonw.exe") Then
                FindSignedPythonW = subFolder.Path & "\pythonw.exe"
                Exit Function
            End If
        Next
    End If

    ' 4. C:\Program Files altındaki Python* klasörlerini tara
    If fso.FolderExists(progFiles) Then
        Set folder = fso.GetFolder(progFiles)
        For Each subFolder In folder.SubFolders
            If Left(LCase(subFolder.Name), 6) = "python" Then
                If IsValidPythonExe(subFolder.Path & "\pythonw.exe") Then
                    FindSignedPythonW = subFolder.Path & "\pythonw.exe"
                    Exit Function
                End If
            End If
        Next
    End If
End Function

Dim pyExe, cmd
pyExe = FindSignedPythonW()

If pyExe <> "" Then
    cmd = """" & pyExe & """ """ & appScript & """"
    WshShell.Run cmd, 0, False
Else
    MsgBox "Novaboard başlatılamadı: Microsoft/Python imzalı Python çalışma zamanı bulunamadı.", 16, "Novaboard - Başlatma Hatası"
End If
