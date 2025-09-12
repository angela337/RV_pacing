Fig2=true
#######################################################################
if $Fig2; then 
# Figure 2: Summary plots for initial device dimensions
	for device in "AveirAR" # "AveirAR" "AveirVR"
	do 
		if [[ $device == "Micra" ]]; then 
			init_len=25.9
		elif [[ $device == "AveirAR" ]]; then 
			init_len=32.2
		elif [[ $device == "AveirVR" ]]; then 
			init_len=38
		fi 
		pngfile=RV_septum_polar_sum_${device}_L${init_len}.png
		cd /data_fast/Work/MS_HF_cohort/images/${device}
		
		#convert \
			#\( RV_Collision/sum_plots/${pngfile} \
			 #PM_Collision/sum_plots/${pngfile} \
			 #TV_Collision/sum_plots/${pngfile} \
			 #sum_plots/Overlay_60_${device}_L${init_len}.png \
			 #+smush -50 \) \		 
		#-resize 30% ${device}_${init_len}_summary_4_AHA.png
		
		clipl=100
		clipr=200
		infile=sum_plots/Overlay_10_${device}_L${init_len}.png
		outfile=temp1.png
		convert "$infile" -crop "$(( $(identify -format %w "$infile") - clipl - clipr ))x$(identify -format %h "$infile")+${clipl}+0" +repage "$outfile"
		#convert "$infile" -crop "$(( $(identify -format %w "$infile") - 2*clip ))x$(identify -format %h "$infile")+${clip}+0" +repage "$outfile"
		
		infile=sum_plots/Overlay_50_${device}_L${init_len}.png
		outfile2=temp2.png
		convert "$infile" -crop "$(( $(identify -format %w "$infile") - clipl ))x$(identify -format %h "$infile")+${clipl}+0" +repage "$outfile2"
		
		#convert \
			#\( PM_Collision/sum_plots/${pngfile} \
			 #TV_Collision/sum_plots/${pngfile} \
			 #$outfile \
			 #$outfile2 \
			 #+smush -50 \) -resize 50% TV_Fig2.png
			 
				
		convert \
			\( RV_Collision/sum_plots/${pngfile} \
			 TV_Collision/sum_plots/${pngfile} \
			 PM_Collision/sum_plots/${pngfile} \
			 $outfile2 \
			 +smush -50 \) -resize 50% Fig2.png
	done
	rm temp*.png
fi 
echo "/data_fast/Work/MS_HF_cohort/images/${device}/Fig2.png"

######################################################################
# Combine all lengths # CSP Fig 3
Fig3=false
if $Fig3; then 
	collision_field='RV_Collision' # Combined_Collision=''
	shift=250
	lshift=200
	#collision_field='TV_Collision'
	#shift=0
	# Figure 3: Micra with different dimensions for combined collision
	for device in "AveirAR" # "AveirAR" "AveirVR"
	do 
		devicePath="/data_fast/Work/MS_HF_cohort/images/${device}"
		
		# Create array to store image paths
		images=()
		for len in {15..45..5}; do
			# Combined Collision # RV_Collision
			#images+=("./${collision_field}/sum_plots/RV_septum_polar_sum_${device}_L${len}.png")
			images+=("${devicePath}/sum_plots/Overlay_50_${device}_L${len}.png")
			#echo "${devicePath}/sum_plots/Overlay_50_${device}_L${len}.png"
		done
		
		# Start with the first image as base
		result_image="${images[0]}"
		
		# For each subsequent image, overlay it on the rightmost 300 pixels
		for ((i=1; i<${#images[@]}; i++)); do
			temp_output="temp_overlay_${i}.png"
			cropped_overlay="temp_cropped_${i}.png"
			
			convert "${images[i]}" -crop +${lshift}+0 "$cropped_overlay"
			
			# Get dimensions of both images
			base_width=$(identify -format "%w" "$result_image")
			base_height=$(identify -format "%h" "$result_image")
			#overlay_width=$(identify -format "%w" "${images[i]}")
			overlay_width=$(identify -format "%w" "$cropped_overlay")
			
			# Calculate new canvas width and overlay position
			overlay_x=$((base_width - ${shift}))
			new_width=$((overlay_x + overlay_width))
			
			# Create expanded canvas and composite images
			#convert -size ${new_width}x${base_height} xc:white \
					#"$result_image" -geometry +0+0 -composite \	
					#"${images[i]}" -geometry +${overlay_x}+0 -composite \			
					#"$temp_output"
			# Create expanded canvas and composite
			convert -size ${new_width}x${base_height} xc:white \
				"$result_image" -geometry +0+0 -composite \
				"$cropped_overlay" -geometry +${overlay_x}+0 -composite \
				"$temp_output"

			# Update result_image for next iteration
			result_image="$temp_output"
		done
		
		# Resize and save final result
		#convert "$result_image" -resize 30% "${device}_all_lengths_${collision_field}.png"
		convert "$result_image" -resize 30% "${devicePath}/${device}_all_lengths.png"
		echo "${devicePath}/${device}_all_lengths.png"
		# Crop 160 pixels from top, resize and save final result
		#convert "$result_image" -crop +0+160 -resize 30% "${device}_all_lengths_combined_collision.png"
		
		# Clean up temporary files
		rm -f temp_overlay_*.png 
		
	done
fi

Fig3_2rows=false


if $Fig3_2rows; then 
    shift=250

    for device in "AveirAR" # "AveirAR" "AveirVR"
    do 
        devicePath="/data_fast/Work/MS_HF_cohort/images/${device}"

        # Collect image paths
        images=()
        for len in {15..45..5}; do
            images+=("${devicePath}/sum_plots/Overlay_50_${device}_L${len}.png")
        done

        # First row (4 images: 15–30 mm)
        montage "${images[0]}" "${images[1]}" "${images[2]}" "${images[3]}" \
            -tile 4x1 -geometry +2+2 temp_row1.png

        # Second row (3 images: 35–45 mm)
        montage "${images[4]}" "${images[5]}" "${images[6]}" \
            -tile 3x1 -geometry +2+2 temp_row2.png

        # Stack the two rows vertically
        montage temp_row1.png temp_row2.png -tile 1x2 -geometry +2+2 \
            -background white temp_combined.png

        # Resize and save final result
        convert temp_combined.png -resize 30% "${devicePath}/${device}_all_lengths.png"
        echo "${devicePath}/${device}_all_lengths.png"

        # Clean up
        rm -f temp_row1.png temp_row2.png temp_combined.png
    done
fi

