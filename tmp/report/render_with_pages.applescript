set inputPath to POSIX file "/Users/calvinbaker/AI_For_Leaders_Module-B-semester-2/CalvinBaker_DX699O2_Final_Project_Module_B.docx"
set outputPath to POSIX file "/Users/calvinbaker/AI_For_Leaders_Module-B-semester-2/CalvinBaker_DX699O2_Final_Project_Module_B_QA.pdf"

tell application "Pages"
    activate
    open inputPath
    set reportDocument to front document
    export reportDocument to outputPath as PDF
    close reportDocument saving no
end tell
