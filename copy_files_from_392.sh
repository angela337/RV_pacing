!/bin/bash

MSHF_path=bioeng392:/data5/alee9/MS_HF_cohort/
#MSHF_path=/data5/alee9/MS_HF_cohort/
#out_MSHF_path=/data_fast/Work/MS_HF_cohort/
for casenum in 01 
do 
	trackingPath=${MSHF_path}/data/${casenum}/2_motion/
	out_trackingPath=${out_MSHF_path}/data/${casenum}/2_motion/
    device=Micra
	for new_length in 15 30 45 
	do 
		for samples in 10 20 30
		do
			for meshsize in 1.5 2 5
			do 	
				devicePath=${trackingPath}/${device}_cone10_${samples}_mesh${meshsize}/
				#out_devicePath5=${trackingPath}/${device}_cone10_${samples}_mesh${meshsize}/
                out_devicePath=${trackingPath}/${device}_cone10_${samples}_mesh${meshsize}/
				
				mkdir -p $out_devicePath
				#mkdir -p $out_devicePath/L${new_length}
				#mv $devicePath $out_devicePath
                
				scp ${devicePath}/L${new_length}/RV_collision* ${out_devicePath}/L${new_length}/ 
			done
		done
	done
done