Fig1E=true
if $Fig1E; then 
    imgdir=/data_fast/Work/MS_HF_cohort/images/
    
    
	convert +append ${imgdir}/AveirAR/sum_plots/Overlay_110_AveirAR_L15_full_AHA.png ${imgdir}/plots/legend_only.png -background white -gravity center ${imgdir}/fig1e.png
	echo "${imgdir}/fig1e.png"
	eog ${imgdir}/fig1e.png
fi 

Fig2=false
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
	echo "/data_fast/Work/MS_HF_cohort/images/${device}/Fig2.png"

fi 

#####################################################################
Fig3=false
if $Fig3; then 
	images=()
	imgdir=/data_fast/Work/MS_HF_cohort/images/plots/
	#/data_fast/Work/MS_HF_cohort/images/plots/PM_Collision_by_AHA_region.png
	for coll in "RV" "TV" "PM" "Combined"
	do 
		images+=(${imgdir}/${coll}_Collision_by_AHA_region.png)
	done
	#echo "${images[1]}"
	convert -append ${images[0]} ${images[1]} ${images[2]} ${images[3]} /data_fast/Work/MS_HF_cohort/images/fig3.png
	echo "/data_fast/Work/MS_HF_cohort/images/fig3.png"
	eog /data_fast/Work/MS_HF_cohort/images/fig3.png
fi

######################################################################
# Combine all lengths # CSP Fig 4
Fig4=false # Length AHA wedge maps 
if $Fig4; then 
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
#####################################################################

Fig4_2rows=false
if $Fig4_2rows; then  # USE THIS
    shift=250

    for device in "AveirAR" # "AveirAR" "AveirVR"
    do 
        devicePath="/data_fast/Work/MS_HF_cohort/images/${device}"

        # Collect image paths
        images=()
        for len in 15 20 25 30 32.2 35 40 45; #{15..45..5}; do
        do
			filename=${devicePath}/sum_plots/Overlay_50_${device}_L${len}.png
			convert $filename -crop 830x1409+180+0 ${devicePath}/sum_plots/temp_L${len}.png
        
            #images+=("${devicePath}/sum_plots/Overlay_50_${device}_L${len}.png")
            images+=(${devicePath}/sum_plots/temp_L${len}.png)
        done

        # First row (4 images: 15–30 mm)
        montage "${images[0]}" "${images[1]}" "${images[2]}" "${images[3]}" \
            -tile 4x1 -geometry +2+2 temp_row1.png

        # Second row (4 images: 35–45 mm)
        montage "${images[4]}" "${images[5]}" "${images[6]}" "${images[7]}" \
            -tile 4x1 -geometry +2+2 temp_row2.png

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
##############################################################################
# CSP pacing line plots for the 4 regions (LB, AB, PB, SB) against the length of the device for the 3 L-PMs
Fig5=false # DO NOT USE THIS
# Version 2 
# CSP pacing - each plot is the L-PM per collision type and all 4 regions are plotted as lines on each plot
Fig5b=false 
Fig5c=false 

if $Fig5; then
	image1=/data_fast/Work/MS_HF_cohort/images/LBBAP_outline.png
	image2=/data_fast/Work/MS_HF_cohort/images/plots/RV_Collision_by_LBBAP_region.png
	imgdir=/data_fast/Work/MS_HF_cohort/images/plots/
	convert +append $image1 $image2 ${imgdir}/LBBAP_RV.png
	
	image1=/data_fast/Work/MS_HF_cohort/images/LBBAP_outline_blank.png
	for coll in "TV" "PM" "Combined"
	do 		
		image2=/data_fast/Work/MS_HF_cohort/images/plots/${coll}_Collision_by_LBBAP_region.png
		convert +append $image1 $image2 ${imgdir}/LBBAP_${coll}.png
	done
	
	convert -append ${imgdir}/LBBAP_RV.png ${imgdir}/LBBAP_TV.png ${imgdir}/LBBAP_PM.png ${imgdir}/LBBAP_Combined.png /data_fast/Work/MS_HF_cohort/images/fig5.png
	echo "/data_fast/Work/MS_HF_cohort/images/fig5.png"
	#rm temp*.png
	
fi 
if $Fig5b; then
	append="regions_as_lines_LBBAP_regions" #  vs "by_LBBAP_region"
	
	convert /data_fast/Work/MS_HF_cohort/images/AveirAR//sum_plots/Overlay_110_AveirAR_L15.png -crop 900x1410+240+0 /data_fast/Work/MS_HF_cohort/images/LBBAP_outline.png
	convert -size 900x1410 xc:white /data_fast/Work/MS_HF_cohort/images/LBBAP_outline_blank.png
	
	image1=/data_fast/Work/MS_HF_cohort/images/LBBAP_outline.png
	image2=/data_fast/Work/MS_HF_cohort/images/plots/RV_Collision_${append}.png
	imgdir=/data_fast/Work/MS_HF_cohort/images/plots/
	convert +append $image1 $image2 ${imgdir}/LBBAP_RV.png
	
	image1=/data_fast/Work/MS_HF_cohort/images/LBBAP_outline_blank.png
	for coll in "TV" "PM" "Combined"
	do 		
		image2=/data_fast/Work/MS_HF_cohort/images/plots/${coll}_Collision_${append}.png
		convert +append $image1 $image2 ${imgdir}/LBBAP_${coll}.png
	done
	
	convert -append ${imgdir}/LBBAP_RV.png ${imgdir}/LBBAP_TV.png ${imgdir}/LBBAP_PM.png ${imgdir}/LBBAP_Combined.png /data_fast/Work/MS_HF_cohort/images/fig5b.png
	echo "/data_fast/Work/MS_HF_cohort/images/fig5b.png"
	#rm temp*.png
	
fi 
if $Fig5c; then # USE THIS ONE
	append="regions_as_lines_LBBAP_regions" #  vs "by_LBBAP_region"
	
	convert /data_fast/Work/MS_HF_cohort/images/AveirAR//sum_plots/Overlay_110_AveirAR_L15.png -crop 900x1410+240+0 /data_fast/Work/MS_HF_cohort/images/LBBAP_outline.png
	convert -size 900x1410 xc:white /data_fast/Work/MS_HF_cohort/images/LBBAP_outline_blank.png
	
	# Create 2-row versions (scaled to 1800x2820)
	
	#convert /data_fast/Work/MS_HF_cohort/images/LBBAP_outline.png -resize 1800x2820! /data_fast/Work/MS_HF_cohort/images/LBBAP_outline_2row.png
	#convert -size 1800x2820 xc:white /data_fast/Work/MS_HF_cohort/images/LBBAP_outline_blank_2row.png
	convert /data_fast/Work/MS_HF_cohort/images/LBBAP_outline.png -resize 1200x1880! /data_fast/Work/MS_HF_cohort/images/LBBAP_outline_2row.png
	convert -size 1200x1880 xc:white /data_fast/Work/MS_HF_cohort/images/LBBAP_outline_blank_2row.png
	# Find the maximum width
	max_width=$(identify -format "%w\n" /data_fast/Work/MS_HF_cohort/images/plots/legend_only.png /data_fast/Work/MS_HF_cohort/images/LBBAP_outline_2row.png | sort -nr | head -1)

	# Pad both images to the maximum width with white background
	convert /data_fast/Work/MS_HF_cohort/images/plots/legend_only.png -background white -gravity center -extent ${max_width}x /data_fast/Work/MS_HF_cohort/images/plots/legend_only_padded.png
	convert /data_fast/Work/MS_HF_cohort/images/LBBAP_outline_2row.png -background white -gravity center -extent ${max_width}x /data_fast/Work/MS_HF_cohort/images/plots/background_padded.png

	# Append vertically (legend on top)
	convert /data_fast/Work/MS_HF_cohort/images/plots/background_padded.png  /data_fast/Work/MS_HF_cohort/images/plots/legend_only_padded.png -append /data_fast/Work/MS_HF_cohort/images/plots/combined_legend_top.png
	
	#image1=/data_fast/Work/MS_HF_cohort/images/LBBAP_outline_2row.png
	image1=/data_fast/Work/MS_HF_cohort/images/plots/combined_legend_top.png
	image2=/data_fast/Work/MS_HF_cohort/images/plots/RV_Collision_${append}.png
	image3=/data_fast/Work/MS_HF_cohort/images/plots/TV_Collision_${append}.png
	imgdir=/data_fast/Work/MS_HF_cohort/images/plots/
	
	# Stack RV and TV plots vertically, then append to 2-row LBBAP outline
	convert -append $image2 $image3 ${imgdir}/RV_TV_combined.png
	convert +append $image1 ${imgdir}/RV_TV_combined.png ${imgdir}/LBBAP_RV_TV.png
	
	image1=/data_fast/Work/MS_HF_cohort/images/LBBAP_outline_blank_2row.png
	#image1=/data_fast/Work/MS_HF_cohort/images/plots/combined_legend_top.png
	image2=/data_fast/Work/MS_HF_cohort/images/plots/PM_Collision_${append}.png
	image3=/data_fast/Work/MS_HF_cohort/images/plots/Combined_Collision_${append}.png
	
	# Stack PM and Combined plots vertically, then append to blank 2-row LBBAP outline
	convert -append $image2 $image3 ${imgdir}/PM_Combined_stacked.png
	convert +append $image1 ${imgdir}/PM_Combined_stacked.png ${imgdir}/LBBAP_PM_Combined.png
	
	# Final vertical combination
	convert -append ${imgdir}/LBBAP_RV_TV.png ${imgdir}/LBBAP_PM_Combined.png /data_fast/Work/MS_HF_cohort/images/fig5c.png
	echo "/data_fast/Work/MS_HF_cohort/images/fig5c.png"
	eog /data_fast/Work/MS_HF_cohort/images/fig5c.png
	
	# Clean up temporary files
	rm ${imgdir}/RV_TV_combined.png ${imgdir}/PM_Combined_stacked.png
	rm temp*.png /data_fast/Work/MS_HF_cohort/images/plots/legend_only_padded.png /data_fast/Work/MS_HF_cohort/images/plots/background_padded.png
	rm /data_fast/Work/MS_HF_cohort/images/plots/combined_legend_top.png
	
fi
#################################################################################
# Graphical abstract
mainPath="/data_fast/Work/MS_HF_cohort/images/graph_abstract/"

# Create array to store image paths
images=()
graphab=false
if $graphab; then 
	for i in RV TV PM
	do 
		for j in 2 #
		do
			images+=("${mainPath}/GraphAb_${i}${j}.png")
		done
	done
	for ((i=0; i<${#images[@]}; i++)); do
		convert ${images[i]} -fuzz 5% -trim +repage ${images[i]}
	done
fi
graphab_cine=false	

if $graphab_cine; then  
    pushd /data_fast/Work/MS_HF_cohort/data/11/images/motion/cemrgoutput/
    
	#convert axial.png -trim axial.png
#	  \( coronal.png -background black -gravity center -extent x$H \) \

	
    H=$(identify -format "%h\n" axial.png coronal.png sagittal.png | sort -nr | head -n1)
	convert \
	  \( axial.png -background black -gravity center -extent x$H \) \
	  \( sagittal.png -background black -gravity center -extent x$H \) \
	  +append multiplanar.png
  
	convert \( img0.png -trim \) \
			\( img1.png -trim \) \
			\( img2.png -trim \) \
			\( img3.png -trim \) \
			\( img4.png -trim \) \
			\( img5.png -trim \) \
			\( img6.png -trim \) \
			\( img7.png -trim \) \
			\( img8.png -trim \) \
			\( img9.png -trim \) +append cine_stack.png

	#convert \( img0.png -trim \) \
			#\( cine_stack.png -resize $(identify -format "%w" img0.png)x \) -append final.png
	#convert \( multiplanar.png -trim \) \
#			\( cine_stack.png -resize $(identify -format "%w" multiplanar.png)x \) -append final.png

	MP_W=$(identify -format "%w" multiplanar.png)

	convert cine_stack.png -resize ${MP_W}x cine_stack_resized.png
	convert -size ${MP_W}x10 xc:black black_band.png
	convert -size ${MP_W}x50 xc:black black_band50.png	
	convert multiplanar.png -trim \
		black_band50.png \
		cine_stack_resized.png \
		black_band50.png \
		black_band50.png \
		black_band50.png \
		-append final_cine.png
		
	 rm  cine_stack*.png multiplanar.png black_band*.png 
	 eog final_cine.png
	popd
fi
