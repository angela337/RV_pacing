mainPath="/data5/alee9/Dropbox/Work/ct-crt/MS_HF_cohort/"
#########################
getGradientImg=false
getScreenShot=false
################################
# getGradientImg=true
getScreenShot=true

for case in 01 #{20..24}
do 

    dcmfile="$mainPath/data/${case}/RV/dcm-0.nii"
    maskfile="$mainPath/data/${case}/RV/all_labels_mask.nii"
    gradient_nii="$mainPath/data/${case}/RV/dcm_masked_gradient.nii"
    output_png="$mainPath/images/case${case}_segmentation.png"

    if [ "$getGradientImg" = true ]; then
        python /data5/alee9/Dropbox/Work/Atria/code/python/img/process_RV_nii.py --dcmfile $dcmfile --maskfile $maskfile --output $gradient_nii
    fi

    # if [ -f "$gradient_nii" ]; then 
    #     echo "case $gradient_nii exists"
    # else
    #     echo "case $gradient_nii does not exist"
    #     continue
    # fi
    if ${getScreenShot}; then
        if [ -f "$gradient_nii" ]; then 
            echo "$gradient_nii exists, generating screenshot"
            python /data5/alee9/Dropbox/Work/Atria/code/python/img/nii2screenshot.py "$gradient_nii" "$output_png"
        else
            echo "case $gradient_nii does not exist, skipping screenshot generation"
            continue
        fi
    fi    
done
