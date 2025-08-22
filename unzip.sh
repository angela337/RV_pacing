#!/bin/bash

#for i in $(seq -w 01 24); do
    #zipfile="${i}.zip"
    #unzipdir="${i}"

    #if [[ -f "$zipfile" ]]; then
        #echo "Found zip file: $zipfile"

        #if [[ ! -d "$unzipdir" ]]; then
            #echo "Unzipping $zipfile into $unzipdir/"
            #unzip "$zipfile" -d "$unzipdir"
        #else
            #echo "Directory $unzipdir already exists. Skipping unzip."
        #fi
    #else
        #echo "Zip file $zipfile not found. Skipping."
    #fi
#done


#!/bin/bash

#for i in $(seq -w 03 24); do
    #src="${i}/${i}"
    #dest="${i}/"

    #if [[ -d "$src" ]]; then
        #echo "Moving contents of $src to $dest"
        #mv "$src"/* "$dest"
        ##rmdir "$src"  # Remove empty inner directory
    #else
        #echo "Directory $src does not exist. Skipping."
    #fi
#done


#!/bin/bash

csv_file="../data/MS_HF_cohort.csv"  # Replace with your actual CSV filename

# Skip header and read CSV line-by-line
tail -n +2 "$csv_file" | while IFS=',' read -r case segname; do
    case_dir=$(printf "%02d" "$case")
    src_glob="../data/${case_dir}/Segmentation/SRS*/output/${segname}"
    dest="../data/${case_dir}/RV/all_labels_mask.nii"

    # Use glob to resolve wildcard
    src_file=$(ls $src_glob 2>/dev/null | head -n 1)

    if [[ -f "$src_file" ]]; then
        # Ensure RV directory exists
        if [[ ! -d "../data/${case_dir}/RV" ]]; then
            echo "Creating directory ${case_dir}/RV"
            mkdir -p "../data/${case_dir}/RV"
        fi

        echo "Moving $src_file to $dest"
        mv "$src_file" "$dest"
    else
        echo "Source file not found for case $case and segname $segname. Skipping."
    fi
done
