
##############################
gradientEdgeDetect=false
label_BP_TV=false
apply_BP_TV_to_vtk=false
getTVring=false
getRVwall=false
CombinePM=false
make_cone=false
flip_mesh=false
motion_tracking=false
getCollision=false
##############################

############# gradientEdgeDetect=True # Done for all already
#label_BP_TV=true # Make downsample image first in cemrgapp
#apply_BP_TV_to_vtk=true # Make 1_seg/BiV_masked.vtk
#getTVring=true
#getRVwall=true

#######
# Manual segmentation 
############### 
#CombinePM=true
# Check vertex for attachment points to chrodae in PM.vtp for Ant, Inf and Sept PM
#############################
#make_cone=true
#flip_mesh=true
motion_tracking=true
#getCollision=true
#############################

# Home paths
MSHF_path=/data_fast/Work/MS_HF_cohort/
python_path=/data_slow/Dropbox/Work/Atria/code/python/vtk_extras
meshtool=/home/alee9/Work/software/meshtool/meshtool 
transform_points=/home/alee9/Work/software/CemrgApp-Linux_v2.3-rc4/bin/MLib/transform-points
transform_image=/home/alee9/Work/software/CemrgApp-Linux_v2.3-rc4/bin/MLib/transform-image

# 392 paths
#MSHF_path=/data5/alee9/MS_HF_cohort/
#python_path=/data5/alee9/Dropbox/Work/Atria/code/python/vtk_extras
#meshtool=/home/carp_2024/CARPentry_ICL_latest/meshtool/meshtool
#transform_points=/data5/alee9/software/CemrgApp-Linux_v2.3-rc4/bin/MLib/transform-points

for casenum in 01 02 04 {06..11} 13 # 02 04 {05..11} 13 # No/bad data or fail at 3,5,12 01
do 
    segPath=${MSHF_path}/data/$casenum/1_seg/
#    segPath=/data5/alee9/MS_HF_cohort/$casenum/RV/
    trackingPath=${MSHF_path}/data/${casenum}/2_motion/
    maskfile=${segPath}/all_labels_mask.nii
    if $gradientEdgeDetect; then 
        echo "# Make masked image and get the gradient edge image "

        dcmfile=${segPath}/dcm-0.nii
        
        outfile=${segPath}/dcm-masked_gradient.nii
        python ${MSHF_path}/code/process_RV_gradient.py ${dcmfile} ${maskfile} ${outfile} --target_labels [4,5,22,24]
    fi 
    
    if $label_BP_TV; then
        # Use CemrgApp to downsample mask image by 2 - reduce image size
        #/data5/alee9/MS_HF_cohort/code/RV_mapping.ipynb
        echo " Make a new image and only extract the BiV and valves in the image /data5/alee9/MS_HF_cohort/data/04/RV/BiV_masked.nii"
        # Make BP 
        #python ${MSHF_path}/code/make_dilated_images.py -maskfile ${segPath}/all_labels_mask_downsample.nii.gz -bp_outfile ${segPath}/BloodPools_Dilated_by_1.nii -biv ${segPath}/BiV_masked.nii -biv_dil ${segPath}/BiV_masked_Dilated_by_1.nii
        #python ${MSHF_path}/code/make_dilated_images.py -maskfile ${segPath}/all_labels_mask.nii -bp_outfile ${segPath}/BloodPools_Dilated_by_1.nii -biv ${segPath}/BiV_masked.nii -biv_dil ${segPath}/BiV_masked_Dilated_by_1.nii
        python ${MSHF_path}/code/make_dilated_images.py -maskfile ${segPath}/all_labels_mask.nii -lv_outfile ${segPath}/LVwall_Dilated_by_1_3_3_3.nii
    fi
    if $apply_BP_TV_to_vtk; then 

        # Convert the image to vtk 
        echo "Convert image to vtk" 
        python ${MSHF_path}/code/nii2vtk2.py ${segPath}/BiV_masked.nii ${segPath}/BiV_masked.vtk 

        echo "Convert to vtk 4.2 version of file"
        python ${python_path}/convertvtk42.py ${segPath}/BiV_masked.vtk ${segPath}/BiV_masked.vtk

        # Dilate image in cemrgapp /data5/alee9/MS_HF_cohort/data/07/RV/BiV_masked_Dilated_by_1.nii
        # IN cemrgapp dilate the masked image and also Bloodpool.nii
        echo "Dilate the BP and label things" 
        python ${python_path}/vtk_scar_map.py ${segPath}/BiV_masked_Dilated_by_1.nii ${segPath}/BiV_masked.vtk ${segPath}/BiV_masked.vtk 
        python ${python_path}/vtk_scar_map.py ${segPath}/BloodPools_Dilated_by_1.nii ${segPath}/BiV_masked.vtk ${segPath}/BiV_masked.vtk 

        python ${python_path}/convertvtk42.py ${segPath}/BiV_masked.vtk ${segPath}/BiV_masked.vtk
        python ${python_path}/vtk_scar_map.py ${segPath}/LVwall_Dilated_by_1_3_3_3.nii ${segPath}/RV_dec_filtered.vtk ${segPath}/RV_dec_filtered.vtk
    fi 
    
# meshtool convert -imsh=${segPath}/BiV_masked -ifmt=vtk -omsh=${segPath}/BiV_masked -ofmt=carp_bin
# meshtool extract surface -msh=${segPath}/BiV_masked -ifmt=carp_bin -op=40 -surf=${segPath}/RV -ofmt=vtk
    
# meshtool resample surfmesh -msh=RV.surfmesh -ifmt=vtk -avrg=10 -outmsh=RV_resample -ofmt=vtk

# python ${python_path}/flip_mesh.py ${segPath}/RV_resample.vtk /data5/alee9/MS_HF_cohort/data/${casenum}/5_motion/RV_resample_flip.vtk

    # Use cemrgapp to segment the PM 

    # In cemrgapp we can open the dcm-masked_gradient and dcm-0.nii and flipping between them we can segment out the RV structure. The best way is use the coupled cross hair rotation and 1st align with with LV long axis. 
    # 1) Go closer to the apex and scroll up to find the moderator band
    # 2) Find the anterior PM in the RV that is connected to the moderator band (closer to the RVOT side)
    # 3) Find the inferior PM (further away from the RVOT)
    # 4) Find the septal PM 
    # Add them all together with elemTag=1
    # python ${python_path}/append_vtk_polydata.py ${segPath}/PM/PM.vtk ${segPath}/BiV_masked.vtk ${segPath}/BiV_masked_PM.vtk --elemTagValue 1 
    if $CombinePM; then 
        #python ${python_path}/append_vtk_polydata.py ${segPath}/PM/ModBand1_3D-interpolation.vtp ${segPath}/PM/ModBand2_3D-interpolation.vtp ${segPath}/PM/ModBand_3D-interpolation.vtp --elemTagValue 1 

        if [[ $casenum==11 ]]; then 
            # For case 11 we have the PM already segmented in the vtp file
            python ${python_path}/append_vtk_polydata.py ${segPath}/PM/ModBand_3D-interpolation.vtp  ${segPath}/PM/InfPM_3D-interpolation.vtp ${segPath}/PM/PM.vtk --elemTagValue 1
            python ${python_path}/append_vtk_polydata.py ${segPath}/PM/SeptPM_3D-interpolation.vtp ${segPath}/PM/PM.vtk ${segPath}/PM/PM.vtk --elemTagValue 1 

        else 

            python ${python_path}/append_vtk_polydata.py ${segPath}/PM/ModBand_3D-interpolation.vtp ${segPath}/PM/AntPM_3D-interpolation.vtp ${segPath}/PM/PM.vtk --elemTagValue 1 
            python ${python_path}/append_vtk_polydata.py ${segPath}/PM/InfPM_3D-interpolation.vtp ${segPath}/PM/PM.vtk ${segPath}/PM/PM.vtk --elemTagValue 1
            python ${python_path}/append_vtk_polydata.py ${segPath}/PM/SeptPM_3D-interpolation.vtp ${segPath}/PM/PM.vtk ${segPath}/PM/PM.vtk --elemTagValue 1 
        fi
        
        # echo "Add in segmentations of the PM and moderator band" 
        python ${python_path}/convertvtk42.py ${segPath}/PM/PM.vtk  ${segPath}/PM/PM.vtk 
        ${meshtool} resample surfmesh -msh=${segPath}/PM/PM -ifmt=vtk -ofmt=vtk_polydata -outmsh=${segPath}/PM/PM_dec -avrg=2


        #python ${python_path}/convertvtk42.py ${segPath}/PM/PM_dec.vtk  ${segPath}/PM/PM_dec.vtk 
    fi

    if $getTVring; then 
        #${meshtool} extract surface -msh=${segPath}/BiV_masked -ifmt=vtk -op=30-40 -surf=${segPath}/TV -ofmt=vtk # carp_txt for vtx file, vtk to visualise"
        
        python ${MSHF_path}/code/nii2vtk2.py ${segPath}/all_labels_mask.nii ${segPath}/TV.vtk --values 22 # this automatically sets the elemTag=1        
        ${meshtool} resample surfmesh -msh=${segPath}/TV -ifmt=vtk -ofmt=vtk_polydata -outmsh=${segPath}/TV -avrg=2 
        
    fi 
    if $getRVwall; then 
        ${meshtool} extract surface -msh=${segPath}/BiV_masked -ifmt=vtk -op=40 -surf=${segPath}/RV_wall -ofmt=vtk_polydata # carp_txt for vtx file, vtk to visualise"
        ${meshtool} smooth mesh -msh=${segPath}/RV_wall.surfmesh -tags=40 -outmsh=${segPath}/RV_smooth -ifmt=vtk -ofmt=vtk_polydata -smth=0.7
        python ${python_path}/vtk_scar_map.py ${segPath}/LVwall_Dilated_by_1_3_3_3.nii ${segPath}/RV_smooth.vtk ${segPath}/RV_smooth.vtk 
        
        ${meshtool} resample surfmesh -msh=${segPath}/RV_smooth -outmsh=${segPath}/RV_dec -ifmt=vtk -ofmt=vtk_polydata -avrg=5
        #rm ${segPath}/RV_wall*  #${segPath}/RV_smooth* 
        # Remove the small elements 
        python ${python_path}/remove_small_cells.py -msh ${segPath}/RV_dec.vtk -cell_area_min 1 -outmsh ${segPath}/RV_dec_filtered.vtk
        # Separate the RV wall and septum
        #python ${python_path}/vtk_scar_map.py ${segPath}/LVwall_Dilated_by_1_3_3_3.nii ${segPath}/RV_dec.vtk ${segPath}/RV_dec.vtk 

    fi
    INDEX_FILE="${MSHF_path}/data/cone_indices_on_PMvtp.csv"
    if [ "$make_cone" = true ]; then 
        # Find the matching line in the CSV
        match=$(awk -F, -v c="$casenum" 'NR>1 && $1==c {print}' "$INDEX_FILE")

        if [ -z "$match" ]; then
            echo "No index data found for case $casenum"
            continue
        fi

        IFS=',' read -r case ant_idx inf_idx sept_idx <<< "$match"

        echo "Processing case $case with indices: Ant=$ant_idx, Inf=$inf_idx, Sept=$sept_idx"



        python ${python_path}/make_cone.py \
            "${segPath}/TV.surfmesh.vtk" "${segPath}/PM/PM.vtk" "${segPath}/PM/Ant_cone.vtp" --index "$ant_idx"

        python ${python_path}/make_cone.py \
            "${segPath}/TV.surfmesh.vtk" "${segPath}/PM/PM.vtk" "${segPath}/PM/Inf_cone.vtp" --index "$inf_idx"

        python ${python_path}/make_cone.py \
            "${segPath}/TV.surfmesh.vtk" "${segPath}/PM/PM.vtk" "${segPath}/PM/Sept_cone.vtp" --index "$sept_idx"


        python ${python_path}/append_vtk_polydata.py ${segPath}/PM/Sept_cone.vtp ${segPath}/PM/Ant_cone.vtp ${segPath}/PM/cone.vtp --elemTagValue 1
        python ${python_path}/append_vtk_polydata.py ${segPath}/PM/Inf_cone.vtp ${segPath}/PM/cone.vtp ${segPath}/PM/cone.vtp --elemTagValue 1

        python ${python_path}/append_vtk_polydata.py ${segPath}/PM/PM_dec.vtk ${segPath}/BiV_masked.vtk ${segPath}/BiV_masked_PM.vtk --elemTagValue 1 
        python ${python_path}/append_vtk_polydata.py ${segPath}/PM/cone.vtp ${segPath}/BiV_masked_PM.vtk ${segPath}/BiV_masked_PM.vtk --elemTagValue 1
    fi

    if $flip_mesh; then 

        mkdir -p ${trackingPath}
        mkdir -p ${trackingPath}/tracked/ 
        echo "Flip mesh to use in motion tracking" 
        #python ${python_path}/convertvtk42.py ${segPath}/PM/PM_dec.vtk  ${segPath}/PM/PM_dec.vtk 
        python ${python_path}/append_vtk_polydata.py ${segPath}/TV.vtk ${segPath}/PM/cone.vtp  ${segPath}/PM/TV_cone.vtp  --elemTagValue 1

        python ${python_path}/append_vtk_polydata.py ${segPath}/TV.vtk ${segPath}/BiV_masked_PM.vtk ${segPath}/BiV_masked_PM.vtk --elemTagValue 2
        echo "Flip the mesh to use in motion tracking" 
        python ${python_path}/flip_mesh.py ${segPath}/BiV_masked_PM.vtk ${MSHF_path}/data/${casenum}/2_motion/BiV_masked_PM_flip.vtk
        python ${python_path}/flip_mesh.py ${segPath}/RV_dec_filtered.vtk ${MSHF_path}/data/${casenum}/2_motion/RV_dec_flip.vtk
        python ${python_path}/flip_mesh.py ${segPath}/RV_smooth.vtk ${MSHF_path}/data/${casenum}/2_motion/RV_smooth_flip.vtk
        python ${python_path}/flip_mesh.py ${segPath}/PM/PM_dec.vtk ${MSHF_path}/data/${casenum}/2_motion/PM_flip.vtk

        python ${python_path}/convertvtk42.py ${segPath}/PM/cone.vtk ${segPath}/PM/cone.vtk
        meshtool resample surfmesh -msh=${segPath}/PM/cone -ifmt=vtk -avrg=2 -outmsh=${segPath}/PM/coneHR -ofmt=vtk
        python ${python_path}/flip_mesh.py ${segPath}/PM/coneHR.vtk ${MSHF_path}/data/${casenum}/2_motion/TV_flip.vtk
        #python ${python_path}/flip_mesh.py ${segPath}/PM/cone.vtk ${MSHF_path}/data/${casenum}/2_motion/TV_flip.vtk
        
        python ${python_path}/flip_mesh.py ${segPath}/TV.surfmesh.vtk ${MSHF_path}/data/${casenum}/2_motion/TV_surfmesh_flip.vtk
    fi      

    

    #ls 
    if $motion_tracking; then 



        # python ${python_path}/flip_mesh.py ${segPath}/BiV_masked_PM.vtk ${MSHF_path}/data/${casenum}/2_motion/BiV_masked_flip.vtk
        # python ${python_path}/flip_mesh.py ${segPath}/RV_dec_filtered.vtk ${MSHF_path}/data/${casenum}/2_motion/RV_dec_flip.vtk
        # python ${python_path}/flip_mesh.py ${segPath}/RV_smooth.vtk ${MSHF_path}/data/${casenum}/2_motion/RV_smooth_flip.vtk
        # python ${python_path}/flip_mesh.py ${segPath}/PM/PM_dec.vtk ${MSHF_path}/data/${casenum}/2_motion/PM_flip.vtk
        # python ${python_path}/flip_mesh.py ${segPath}/PM/TV_cone.vtp ${MSHF_path}/data/${casenum}/2_motion/TV_flip.vtk
        
        # python ${python_path}/flip_mesh.py ${segPath}/TV.surfmesh.vtk ${MSHF_path}/data/${casenum}/2_motion/TV_surfmesh_flip.vtk

        startTime=0
        init_mesh=${MSHF_path}/data/${casenum}/2_motion/BiV_masked_flip.vtk
        RVinit_mesh=${MSHF_path}/data/${casenum}/2_motion/RV_dec_flip.vtk
        RVsmthinit_mesh=${MSHF_path}/data/${casenum}/2_motion/RV_smooth_flip.vtk
        PMinit_mesh=${MSHF_path}/data/${casenum}/2_motion/PM_flip.vtk
        TVinit_mesh=${MSHF_path}/data/${casenum}/2_motion/TV_flip.vtk
        tsffd=${trackingPath}/tsffd.dof
        #for frame in 0 4    
        for (( frame = 1; frame<=10; frame++))
        do    
            echo $frame                                    
            frame10=$((frame*10))
            # Whole mesh
            #${transform_points}  ${init_mesh} ${trackingPath}/tracked/transformed-${frame}.vtk -dofin ${tsffd} -ascii -St ${frame10} -Tt ${startTime} -verbose 3 
            # RV wall 
            #${transform_points}  ${RVinit_mesh} ${trackingPath}/tracked/RV_dec-${frame}.vtk -dofin ${tsffd} -ascii -St ${frame10} -Tt ${startTime} -verbose 3 
            #${transform_points}  ${RVsmthinit_mesh} ${trackingPath}/tracked/RV_smth-${frame}.vtk -dofin ${tsffd} -ascii -St ${frame10} -Tt ${startTime} -verbose 3 
            # PM
            #${transform_points}  ${PMinit_mesh} ${trackingPath}/tracked/PM-${frame}.vtk -dofin ${tsffd} -ascii -St ${frame10} -Tt ${startTime} -verbose 3 
            # TV 
            #${transform_points}  ${TVinit_mesh} ${trackingPath}/tracked/TV-${frame}.vtk -dofin ${tsffd} -ascii -St ${frame10} -Tt ${startTime} -verbose 3
            #${transform_points}  ${trackingPath}/TV_surfmesh_flip.vtk ${trackingPath}/tracked/TV_ring-${frame}.vtk -dofin ${tsffd} -ascii -St ${frame10} -Tt ${startTime} -verbose 3
            # transform image for figure generation - use case11 - open in cemrgapp and then write out axial view
            #${transform_image} ${maskfile} ${trackingPath}/tracked/mask-${frame}.nii -dofin ${tsffd} -St ${frame10} -Tt ${startTime}

        done  
    fi 
    
    # if [[ ! -d  ${trackingPath}/tracked/ ]]; then 
        
    #     #mv ${trackingPath}/RV_dec-*.vtk ${trackingPath}/tracked/ 
    #     #mv ${trackingPath}/RV_smth-*.vtk ${trackingPath}/tracked/ 
    #     #mv ${trackingPath}/transformed-*.vtk ${trackingPath}/tracked/ 
    # fi 
    
    # if $getCollision; then 
    #     mkdir -p ${trackingPath}/RV_struct/
    #     mkdir -p ${trackingPath}/RV_wall/
    #     echo "Calculate collision for resampled 100 points from RV wall for case ${casenum}" 
    #     #for (( frame = 0; frame<=10; frame++))
    #     for frame in 4 #{0..10}
    #     do  
    #         echo "Calculate RV wall collision for case ${casenum}: time $frame"
    #         #if [[ ! -f ${trackingPath}/RV_wall/mesh-${frame}.vtp ]]; then 
    #         python ${python_path}/motion_collision_elem_efficient.py -transformedfile ${trackingPath}/tracked/transformed-${frame}.vtk -RVwallfile ${trackingPath}/tracked/RV_dec-${frame}.vtk -RVwallfile_smth ${trackingPath}/tracked/RV_smth-${frame}.vtk -outfile  ${trackingPath}/RV_wall/mesh-${frame}.vtp -outptfile ${trackingPath}/RV_wall/pt-${frame}.vtp -collision_target_tags "40" -vv --no-multiprocessing 
    #         #fi
    #         echo "Finished RV wall collision calc for case ${casenum}: time $frame"            

    #         if [[ ! -f ${trackingPath}/RV_struct/mesh-${frame}.vtp ]]; then 
    #             echo "Calculate RV struct collision for time $frame"
    #         #    python ${python_path}/motion_collision_elem_efficient.py -transformedfile ${trackingPath}/tracked/transformed-${frame}.vtk -RVwallfile ${trackingPath}/tracked/RV_dec-${frame}.vtk -RVwallfile_smth ${trackingPath}/tracked/RV_smth-${frame}.vtk -outfile  ${trackingPath}/RV_struct/mesh-${frame}.vtp -outptfile ${trackingPath}/RV_struct/pt-${frame}.vtp -collision_target_tags "1" #
    #         fi
    #         echo "Finished RV struct collision calc for case ${casenum}: time $frame"
    #     done
    # fi

    #mkdir -p ${trackingPath}/T-PM/ # Simulate transvenous PM 

    if $getCollision; then 
        for device in Micra # AveirAR AveirVR # AveirAR # "Micra": {"D": 6.7, "L": 25.9}, # AV/AV2 Micra #AveirAR # AveirVR 
        do 
            mkdir -p ${trackingPath}/$device/
            # mkdir -p ${trackingPath}/T-PM/$device/
        
            if [[ $device == "Micra" ]]; then 
                init_len=25.9 
            elif [[ $device == "AveirAR" ]]; then 
                init_len=32.2
            elif [[ $device == "AveirVR" ]]; then 
                init_len=38
            elif [[ $device == "TPM" ]]; then 
                init_len=30
            fi

            for new_length in $init_len # 15 20 25 30 35 40 45 
            do
                mkdir -p ${trackingPath}/$device/L${new_length}
                # For the L-PM simulations
                python ${python_path}/RV_collision.py -RV_files ${trackingPath}/tracked/RV_dec- -PM_files ${trackingPath}/tracked/PM- -TV_files ${trackingPath}/tracked/TV- -out_files ${trackingPath}/$device/L${new_length}/RV_collision- -device $device -L ${new_length} -v 

                # For the T-PM simulations
                #mkdir -p ${trackingPath}/T-PM/$device/L${new_length}
                #python ${python_path}/RV_collision.py -RV_files ${trackingPath}/tracked/RV_dec- -PM_files ${trackingPath}/tracked/PM- -TV_files ${trackingPath}/tracked/TV- -out_files ${trackingPath}/T-PM/$device/L${new_length}/RV_collision- -device $device -L ${new_length} -v #-TV_ring_files ${trackingPath}/tracked/TV_ring-

                                
            done
        done
    fi
    echo "Finished running ${MSHF_path}/code/run_RV_sim.sh for MS_HF_cohort data ${casenum}"
done
# To process the results we can use the AHA_mapping.ipynb notebook
# AHA_mapping.ipynb 

# To get the tables we can use the Process_AHA_csv_to_tables.ipynb notebook
# Process_AHA_csv_to_tables.ipynb

# To run the statistical analysis and plot the results we can use the Analysis_compare_csv_output_from_AHA_mapping.ipynb notebook
# Analysis_compare_csv_output_from_AHA_mapping.ipynb

# To map AHA results onto the 3D mesh we can use the Map_3D_mesh.ipynb notebook
# Map_3D_mesh.ipynb

# To get the device specifications and to see the front and back views of the 3D mesh we can use the Device_specs.ipynb notebook
# Device_specs.ipynb