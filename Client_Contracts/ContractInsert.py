#!/usr/bin/python3

LEASEE1 = "LEASEE_ONE_VAR"
LEASEE2 = "LEASEE_TWO_VAR"

replacements = {LEASEE1:"L1", LEASEE2: "L2"}

with open('../templates/contract.html') as infile, open('out_client.html', 'w') as outfile:
    for line in infile:
        for src, target in replacements.items():
            line = line.replace(src, target)
        outfile.write(line)