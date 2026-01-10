#!/usr/bin/env python3

import argparse
import copy
import csv
import os
import plistlib
import sys


# Whether to use lpd or ipp. Defaults to lpd, unless you specify ipp here.
ipp_lpd = 'lpd'

# Default keys for the nopkg. Make sure to change your org's name.
default_keys = {
    'catalogs': ['testing'],
    'category': 'Printers',
    'developer': 'NAME OF YOUR ORG',
    'installer_type': 'nopkg',
    'minimum_os_version': '10.7.0',
    'unattended_install': True,
    'uninstall_method': 'uninstall_script',
    'uninstallable': True
    }


def get_options():
    parser = argparse.ArgumentParser(description='Generate a Munki nopkg-style pkginfo for printer installation.')
    parser.add_argument('--csv', required=True, help='Path to CSV file containing printer info. If CSV is provided, all other options are ignored.')
    args = parser.parse_args()
    if args.csv:
        template_csv = args.csv
    else:
        print("ERROR: --csv argument is required.")
        sys.exit(1)
    return template_csv


def get_options_string(option_list):
    # optionList should be a list item
    options_string = ''
    for option in option_list:
        if option == option_list[0]:
            options_string += f'-o {option.replace(" ", "")}'
        else:
            options_string += f' -o {option.replace(" ", "")}'
    return options_string


def main():
    template_csv = get_options()

    if not os.path.isfile(template_csv):
        print(f"ERROR: {template_csv} doesn't exist")
        sys.exit(1)

    print("Getting current working directory to output nopkg(s) to...")
    cwd = os.getcwd()
    print(f"Got {cwd}. Will output Printer nopkg(s) there.")

    with open(template_csv, mode='r') as infile:
        reader = csv.reader(infile)
        next(reader, None) # skip the header row
        nopkg_contents = copy.deepcopy(default_keys)
        for row in reader:
            # each row contains 10 elements:
            # Printer name, location, display name, address, driver, description, options, version, requires, icon
            # options in the form of "Option=Value Option2=Value Option3=Value"
            # requires in the form of "package1 package2" Note: the space seperator
            printer_name = row[0]
            printer_queue = printer_name.replace(" ", "_")
            printer_location = row[1]
            display_name = row[2]
            nopkg_contents['display_name'] = display_name
            # Check for a protocol listed in the address
            if '://' in row[3]:
                # Assume the user passed in a full address and protocol
                full_address = row[3]
            else:
                # Assume the user wants to use the default, lpd://
                full_address = f'{ipp_lpd}://' + row[3]
            min_address = full_address.split("://")[1]
            # Append the driver path to the driver file specified in the csv
            base_driver = row[4]
            if row[4].endswith('.gz'):
                base_driver = row[4].replace('.gz', '')
            if base_driver.endswith('.ppd'):
                base_driver = base_driver.replace('.ppd', '')
            driver = f'/Library/Printers/PPDs/Contents/Resources/{base_driver}'
            nopkg_contents['description'] = row[5]
            the_option_string = ''
            if row[6] != "":
                options_string = get_options_string(row[6].split(" "))
            nopkg_contents['name'] = "Printer_" + str(printer_name) # set to printer name
            # Check for a version number
            if row[7] != "":
                # Assume the user specified a version number
                version = row[7]
            else:
                # Use the default version of 1.0
                version = "1.0"
            nopkg_contents['version'] = version
            # Add required packages if passed in the csv
            if row[8] != "":
                nopkg_contents['requires'] = row[8].split(' ')
            # Check for an icon
            if row[9] != "":
                nopkg_contents['icon_name'] = row[9]
            # Now change the variables in the installcheck_script
            nopkg_contents['installcheck_script'] = f'#!/bin/zsh\n\nprinter_check=$(/usr/bin/lpstat -s | /usr/bin/grep "{min_address}")\n\nif [[ -z "$printer_check" ]]; then\nexit 0\nelse\nexit 1\nfi\n'
            nopkg_contents['postinstall_script'] = f'#!/bin/zsh\n\n/usr/sbin/lpadmin -p {printer_queue} -L "{printer_location}" -D "{display_name}" -v "{full_address}" -P "{driver}" -E {options_string}'.format()
            # Now change the one variable in the uninstall_script
            nopkg_contents['uninstall_script'] = f'#!/bin/zsh\n\nprinter_name=$(/usr/bin/lpstat -s | /usr/bin/grep -w "{min_address}" | /usr/bin/sed -n \'1 p\' | /usr/bin/awk -F " " \'{{print $3}}\' | /usr/bin/awk -F ":" \'{{print $1}}\')\n\n/usr/sbin/lpadmin -x "$printer_name"\n'
            # Write out the file
            new_file_name = os.path.join(cwd, f"Printer_{printer_name}-{version}.pkginfo")
            if os.path.isfile(new_file_name):
                print(f"WARNING: {new_file_name} already exists, so skipping...")
                continue
            try:
                f = open(new_file_name, 'wb')
            except:
                print(f"ERROR: Unable to open {new_file_name} for writing. Skipping...")
                continue
            try:
                plistlib.dump(nopkg_contents, f)
            except:
                print(f"ERROR: Unable to write contents to {new_file_name}. Skipping...")
                continue
            print(f"Created nopkg {new_file_name}.")
            f.close()


if __name__ == "__main__":
    main()
