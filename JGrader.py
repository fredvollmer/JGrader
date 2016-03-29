import zipfile, os, sys, signal, csv, shutil
from subprocess import call
from colorama import init, Fore, Style

# Initiate colorama, in case some poor soul uses Windows
init()

javaExecutionStatus = False
gradingComplete = True
currentIndex = 0
csvFile = None

def main(filename, mainClass):
    global javaExecutionStatus
    global currentIndex
    global gradingComplete
    global csvFile

    totalAssignemnts = 0
    csvFile = None
    gradeItem = None

    '''try: input = raw_input
    except NameError: pass'''

    print("Welcome to JGrader\n" + Fore.WHITE + "Version 0.1\n\n" +
          Style.RESET_ALL +
          "Unzipping " + filename + "...\n")

    assert zipfile.is_zipfile(filename), "That s not a valid ZIP archive"

    mainZipArchive = zipfile.ZipFile(filename, 'r')

    # Get all objects in this archive
    zips = mainZipArchive.namelist()
    assignmentName = mainZipArchive.filename[:-4]
    for zip in zips[:]:
        filename, ext = os.path.splitext(zip)
        if not ext == ".zip":
            zips.remove(zip)

    totalAssignemnts = len(zips)

    print(str(len(zips)) + " assignments were found.")
    print()
    gradeItem = input("What is the EXACT title of the grade item in D2L associated with this assignment?")

    csvLocation = filename.split("/")

    if len(csvLocation) > 1:
        csvLocation = "/".join(csvLocation[:-1]) + "/"
    else:
        csvLocation = ""

    csvPath = csvLocation + assignmentName

    # Check if file exists
    if os.path.isfile(csvPath + ".csv"):
        while True:
            print(Fore.RED + "A gradebook CSV file already exists for this assignment.\n" +
                Style.RESET_ALL +
                "    [1]: Keep\n" +
                "    [2]: Overwrite")
            choice = input("Pick an option (Default: Keep): ")

            if choice == "1":
                n = 1
                while os.path.isfile(csvPath + ".csv"):
                    csvPath = assignmentName + "-" + str(n)
                    n += 1
                break

            elif choice == "2":
                os.remove(csvPath + ".csv")
                break

            else:
                print(Fore.RED + "Invalid choice." + Style.RESET_ALL)

    print()
    print("Where do you want to begin?")
    print("    [1]: Start from first assignment")
    print("    [2]: Start with the nth assignment")
    print()
    choice = input("Pick an option: ")

    if choice == "2":
        print("What number assignment would you like to start with?")
        n = input("Enter a number between 1 and " + str(totalAssignemnts) + " ")
        while not 0 < int(n) <= totalAssignemnts:
            print(Fore.RED + "Invalid choice" + Style.RESET_ALL)
            n = input("Enter a number between 1 and " + str(totalAssignemnts))
        zips = zips[int(n)-1:-1]
        currentIndex = int(n)

    csvFile = open(csvPath + ".csv", "a+")
    csvWriter = csv.writer(csvFile, quoting=csv.QUOTE_MINIMAL)
    csvReader = csv.reader(csvFile, delimiter=",")
    csvData = list(csvReader)

    # Create header row if needed
    if (len(csvData)) < 1:
        csvWriter.writerow(["Username", gradeItem + " Points Grade", "Comment", "End-of-Line Indicator"])

    gradingComplete = False

    for zipName in zips:
        currentIndex += 1

        # Remove temp data
        shutil.rmtree("jGraderTempData", ignore_errors=True)

        # Get meta from filename
        meta = zipName.split(" - ")
        studentID = meta[0].split("/")[-1]
        studentName = meta[1].split(" ")
        studentName = ", ".join(studentName)

        zipPath = mainZipArchive.extract(zipName, "jGraderTempData")

        # Make sure this is a zip file
        if not zipfile.is_zipfile(zipPath):
            print(Fore.RED + "********** Error reading zip file for " + studentName + " **********" + Style.RESET_ALL)
            input("Press <Enter> to continue to next student.")
            continue

        # Get source files
        zipObject = zipfile.ZipFile(zipPath)

        # Test zip file for errors
        if zipObject.testzip():
            # File is corrput
            print(Fore.RED + "********** Error reading zip file for " + studentName + " **********" + Style.RESET_ALL)
            input("Press <Enter> to continue to next student.")
            continue

        # Get source filenames
        zipObject.extractall("jGraderTempData/raw")

        sourceFiles = [os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(os.getcwd() + "/jGraderTempData/raw")
            for f in files if f.endswith('.java')]

        # Compute relative path to source directory
        sourcePath = "/".join(sourceFiles[0].split("/")[:-1])
        sourcePath = sourcePath.split(os.getcwd() + "/")[-1]

        # Compute package name from directory structure
        package = sourcePath.split("/")[-1]

        # Temp variable for mainClass, so it can be altered for this student only
        _mainClass = mainClass

        while True:
            print(Fore.BLUE + "\nStudent " + str(currentIndex) + " of " + str(totalAssignemnts) + ": " +
                  studentName + "\n-------------------------------------")
            print(Fore.GREEN + "    Actions:" + Style.RESET_ALL)
            print("    [r]: Run program")
            print("    [g]: Enter grade")
            print("    [p]: Change package name (for this student only)")
            print("    [m]: Change main class name (for this student only)")
            print("    [n]: Next assignment")
            print(Fore.GREEN + "    View source files:" + Style.RESET_ALL)
            n = 0
            for sourceFile in sourceFiles:
                print("    [" + str(n) + "]: " + sourceFile.split("/")[-1])
                n += 1

            choice = input("Enter a choice: ")

            if choice == "r":
                # Compile
                print("Compiling...")

                # Run path is path minus last folder, since that's part of class name
                # If package name is empty, include last folder in runPath
                runPath = "/".join(sourcePath.split("/")[:-1]) if len(package) > 0 else "/".join(sourcePath.split("/"))

                fullClassName = package + "." + _mainClass if len(package) > 0 else _mainClass
                call("javac '" + sourcePath + "'/*.java", shell=True)
                # Run program
                print(Fore.GREEN + "*********** BEGIN PROGRAM OUTPUT ***********")
                print(Fore.MAGENTA)
                javaExecutionStatus = True
                call(["java", "-Djava.security.manager", "-cp", runPath, fullClassName])
                javaExecutionStatus = False
                print(Fore.GREEN + "************ END PROGRAM OUTPUT ************")
                print(Style.RESET_ALL)

            elif choice == "p":
                package = input("Enter new package name: ")

            elif choice == "m":
                _mainClass = input("Enter main class name: ")

            elif choice == "g":
                score = input("Enter score: ")
                comment = input("Enter comment: ")
                csvWriter.writerow([studentName, score, comment, "#"])
                break

            elif choice == "n":
                break

            elif int(choice) in range(0, len(sourceFiles)):
                sourcePath = sourceFiles[int(choice)]
                EDITOR = os.environ.get('EDITOR','vim') #that easy!

                call([EDITOR, sourcePath])

            else:
                print("Invalid choice.")

    if currentIndex > totalAssignemnts:
        gradingComplete = True

    # Close CSV file
    csvFile.close()

def sigint_handler(signum, frame):
    global javaExecutionStatus
    global gradingComplete
    global currentIndex
    global csvFile
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    #signal.signal(signal.SIGINT, original_sigint)
    if javaExecutionStatus:
        print(Fore.RED + "\nJava program terminated." + Style.RESET_ALL)
    else:
        print("\nAdios!")
        if not gradingComplete:
            print("To continue where you left off, choose option 2 at startup and enter " +
                  str(currentIndex) + ".")
        if csvFile:
            csvFile.close()
        sys.exit(1)

    # restore the exit gracefully handler here
    #signal.signal(signal.SIGINT, exit_gracefully)

if __name__ == '__main__':
    # store the original SIGINT handler
    #original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, sigint_handler)
    main(sys.argv[1], sys.argv[2])
