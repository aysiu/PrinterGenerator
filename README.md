PrinterGenerator
================

This script will generate a ["nopkg"](https://github.com/munki/munki/wiki/nopkgs)-style pkginfo file for [Munki](https://github.com/munki/munki/wiki) to install a printer.

See [Managing Printers with Munki](https://github.com/munki/munki/wiki/Managing-Printers-With-Munki) for more details.

## Usage

The script takes as an argument a CSV file containing a list of printers with all the necessary information.  

The script will generate a pkginfo file. This pkginfo file is a "nopkg" style, and thus has three separate scripts:  

* installcheck_script
* postinstall_script
* uninstall_script

The installcheck_script looks for an existing printer with the address (lpd:// or ipp://). If it does not find one, it will exit 0 and trigger an installation request.

The postinstall_script will attempt to create the printer using the `lpadmin` command.

The uninstall_script will delete the printer with the address (lpad:// or ipp://) if uninstallation is triggered.

### Using a CSV file:

A template CSV file is provided to make it easy to generate multiple pkginfos in one run.  Pass the path to the csv file with `--csv`:

```
python3 print_generator.py --csv /path/to/printers.csv
```
The script will try to create a nopkg with a name based on the printer name and version you specify in the CSV. If that file already exists, the script will warn you and then skip creating the file.

The CSV file's columns should be pretty self-explanatory:

* Printer name: Name of the print queue
* Location: The "location" of the printer
* Display name: The visual name that shows up in the Printers & Scanners pane of the System Preferences, and in the print dialogue boxes.  Also used in the Munki pkginfo.
* Address: The IP or DNS address of the printer. The template uses the form: `lpr://ADDRESS`.  Change to another protocol in the template if necessary.
* Driver: Name of the driver file in /Library/Printers/PPDs/Contents/Resources/.
* Description: Used only in the Munki pkginfo.
* Options: Any printer options that should be specified. These **must** be space-delimited key=value pairs, such as "HPOptionDuplexer=True OutputMode=normal".  **Do not use commas to separate the options, because this is a comma-separated values file.**
* Version: Used only in the Munki pkginfo.
* Requires: Required packages for Munki pkginfo. These **must** be space-delimited, such as "CanonDriver1 CanonDriver2".
* Icon: Optionally specify an existing icon in the Munki repo to display for the printer in Managed Software Center.

The CSV file is not sanity-checked for invalid entries or blank fields, so double check your file and test your pkginfos thoroughly.

### Figuring out options:

Printer options can be determined by using `lpoptions` on an existing printer queue:  
`/usr/bin/lpoptions -p YourPrinterQueueName -l`  

Here's a snip of output:

```
OutputMode/Quality: high-speed-draft fast-normal *normal best highest
HPColorMode/Color: *colorsmart colorsync grayscale
ColorModel/Color Model: *RGB RGBW
HPPaperSource/Source: *Tray1
Resolution/Resolution: *300x300dpi 600x600dpi 1200x1200dpi
```

Options typically have the actual PPD option name on the left side of the /, and a display name (which is likely to show up in the printer settings dialogue boxes) on the right of the /.  The possible values for the printer are listed after the colon.  The current option is marked with an "*".  

Despite `lpoptions` using a "Name/Nice Name: Value *Value Value" format, the option must be specified more strictly:  
"HPColorMode=grayscale"

This is the format you must use when passing options to `--options`, or specifying them in the CSV file.  

*Note that `/usr/bin/lpoptions -l` without specifying a printer will list options for the default printer.*


### Example:
```
/usr/local/bin/managed_python3 print_generator.py --csv Template.csv
```

The output pkginfo file generated (using the unmodified Template.csv):

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>catalogs</key>
	<array>
		<string>testing</string>
	</array>
	<key>category</key>
	<string>Printers</string>
	<key>description</key>
	<string>Black and white printer in Tech Office</string>
	<key>developer</key>
	<string>NAME OF YOUR ORG</string>
	<key>display_name</key>
	<string>My Printer Queue</string>
	<key>icon_name</key>
	<string>HP LaserJet 4250.icns</string>
	<key>installcheck_script</key>
	<string>#!/bin/zsh

printer_check=$(/usr/bin/lpstat -s | /usr/bin/grep "10.0.0.1")

if [[ -z "$printer_check" ]]; then
exit 0
else
exit 1
fi
</string>
	<key>installer_type</key>
	<string>nopkg</string>
	<key>minimum_os_version</key>
	<string>10.7.0</string>
	<key>name</key>
	<string>Printer_MyPrinterQueue</string>
	<key>postinstall_script</key>
	<string>#!/bin/zsh

/usr/sbin/lpadmin -p MyPrinterQueue -L "Tech Office" -D "My Printer Queue" -v "lpd://10.0.0.1" -P "/Library/Printers/PPDs/Contents/Resources/HP officejet 5500 series" -E -o HPOptionDuplexer=True -o OutputMode=normal</string>
	<key>requires</key>
	<array>
		<string>HPPrinterDriver</string>
	</array>
	<key>unattended_install</key>
	<true/>
	<key>uninstall_method</key>
	<string>uninstall_script</string>
	<key>uninstall_script</key>
	<string>#!/bin/zsh

printer_name=$(/usr/bin/lpstat -s | /usr/bin/grep -w "10.0.0.1" | /usr/bin/sed -n '1 p' | /usr/bin/awk -F " " '{print $3}' | /usr/bin/awk -F ":" '{print $1}')

/usr/sbin/lpadmin -x "$printer_name"
</string>
	<key>uninstallable</key>
	<true/>
	<key>version</key>
	<string>1.0</string>
</dict>
</plist>
```
