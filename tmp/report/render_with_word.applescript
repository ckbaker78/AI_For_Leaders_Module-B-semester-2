set inputPath to POSIX file "/Users/calvinbaker/AI_For_Leaders_Module-B-semester-2/CalvinBaker_DX699O2_Final_Project_Module_B.docx"
set outputPath to (POSIX file "/Users/calvinbaker/AI_For_Leaders_Module-B-semester-2/CalvinBaker_DX699O2_Final_Project_Module_B_QA.pdf") as text

tell application "Microsoft Word"
    activate
    if exists document "CalvinBaker_DX699O2_Final_Project_Module_B.docx" then
        set reportDocument to document "CalvinBaker_DX699O2_Final_Project_Module_B.docx"
    else
        open inputPath
        set reportDocument to active document
    end if
    tell reportDocument
        save as it file name outputPath file format format PDF
    end tell
    close reportDocument saving no
end tell
