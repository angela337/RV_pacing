##!/bin/bash

#csv_file="../data/MS_HF_cohort.csv"  # Replace with your actual CSV filename

## Skip header and read CSV line-by-line
#tail -n +2 "$csv_file" | while IFS=',' read -r case segname; do
    #case_dir=$(printf "%02d" "$case")
    #src_glob="../data/${case_dir}/Segmentation/*/output/${segname}"
    #echo "$src_glob"
    #dest="../data/${case_dir}/RV/all_labels_mask.nii"

    ## Use glob to resolve wildcard
    #src_file=$(ls $src_glob 2>/dev/null | head -n 1)

    #if [[ -f "$src_file" ]]; then
        ## Ensure RV directory exists
        #if [[ ! -d "../data/${case_dir}/RV" ]]; then
            #echo "Creating directory ${case_dir}/RV"
            #mkdir -p "../data/${case_dir}/RV"
        #fi

        #echo "Moving $src_file to $dest"
        #mv "$src_file" "$dest"
        ##
    #else
        #echo "Source file not found for case $case and segname $segname. Skipping."

    #fi
#done

for case in  02 {04..24} 
do 
	destdir="../data/${case}/RV/"
	srcfile="../zipped/CT_nii/${case}/dcm-0.nii"
	echo "cp ${srcfile} ${destdir}"
	cp ${srcfile} ${destdir}
	
done
