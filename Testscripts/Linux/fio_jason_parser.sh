# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the Apache License.
. utils.sh || {
	echo "Error: missing utils.sh file."
	exit 10
}
csv_file=perf_fio.csv
csv_file_tmp=output_tmp.csv
echo $file_name
echo $csv_file
rm -rf $csv_file
echo "Iteration,TestType,BlockSize,Threads,Jobs,TotalIOPS,ReadIOPS,MaxOfReadMeanLatency,ReadMaxLatency,ReadBw,WriteIOPS,MaxOfWriteMeanLatency,WriteMaxLatency,WriteBw" > $csv_file_tmp

if [ $DISTRO_NAME == "centos" ] || [ $DISTRO_NAME == "rhel" ] || [ $DISTRO_NAME == "oracle" ] || [ $DISTRO_NAME == "almalinux" ] || [ $DISTRO_NAME == "rockylinux" ]; then
    if [[ $DISTRO_VERSION =~ ^6\. ]]; then
        yum -y groupinstall "Development Tools"
        wget ftp://gnu.mirror.iweb.com/gawk/gawk-5.0.0.tar.xz
        tar -xvf gawk-5.0.0.tar.xz
        pushd gawk-5.0.0 && ./configure && make && make install > /dev/null 2>&1
        popd
        yes | cp -f /usr/local/bin/gawk /bin/
    fi
fi

bc_cmd=$(echo $(Get_BC_Command))
json_list=($(ls *.json))
count=0
while [ "x${json_list[$count]}" != "x" ]
do
	file_name=${json_list[$count]}
	Iteration=$(echo -e $file_name |gawk -f JSON.awk|grep '"jobname"'| tail -1| sed 's/.*]//'| sed 's/[[:blank:]]//g'| sed 's/"iteration\(.*\)"/\1/')
	Jobs=$(echo -e $file_name |awk -f JSON.awk|grep '"jobname"'| wc -l)
	ReadIOPS=$(echo -e $file_name |awk -f JSON.awk|grep '"read","iops"'| sed 's/.*]//' | paste -sd+ - | ${bc_cmd})
	MaxOfReadMeanLatency=$(echo -e $file_name |awk -f JSON.awk|grep '"read","lat","mean"'| sed 's/.*]//'| sed 's/[[:blank:]]//g'|sort -g|tail -1)
	if [[ $MaxOfReadMeanLatency == '' ]];then
		MaxOfReadMeanLatency=$(echo -e $file_name |awk -f JSON.awk|grep '"read","lat_ns","mean"' | sed 's/.*]//'| sed 's/[[:blank:]]//g'|sort -g|tail -1|awk '{print $1/1000}')
	fi

	ReadMaxLatency=$(echo -e $file_name |awk -f JSON.awk|grep '"read","lat","max"'| sed 's/.*]//'| sed 's/[[:blank:]]//g'|sort -g|tail -1)
	if [[ $ReadMaxLatency == '' ]];then
		ReadMaxLatency=$(echo -e $file_name |awk -f JSON.awk|grep '"read","lat_ns","max"' | sed 's/.*]//'| sed 's/[[:blank:]]//g'|sort -g|tail -1|awk '{print $1/1000}')
	fi

	ReadBw=$(echo -e $file_name |awk -f JSON.awk|grep '"read","bw"'| sed 's/.*]//'| sed 's/[[:blank:]]//g'| paste -sd+ - | ${bc_cmd})
	WriteIOPS=$(echo -e $file_name |awk -f JSON.awk|grep '"write","iops"'| sed 's/.*]//' | paste -sd+ - | ${bc_cmd})
	MaxOfWriteMeanLatency=$(echo -e $file_name |awk -f JSON.awk|grep '"write","lat","mean"'| sed 's/.*]//'| sed 's/[[:blank:]]//g'|sort -g|tail -1)
	if [[ $MaxOfWriteMeanLatency == '' ]];then
		MaxOfWriteMeanLatency=$(echo -e $file_name |awk -f JSON.awk|grep '"write","lat_ns","mean"' | sed 's/.*]//'| sed 's/[[:blank:]]//g'|sort -g|tail -1|awk '{print $1/1000}')
	fi

	WriteMaxLatency=$(echo -e $file_name |awk -f JSON.awk|grep '"write","lat","max"'| sed 's/.*]//'| sed 's/[[:blank:]]//g'|sort -g|tail -1)
	if [[ $WriteMaxLatency == '' ]];then
		WriteMaxLatency=$(echo -e $file_name |awk -f JSON.awk|grep '"write","lat_ns","max"' | sed 's/.*]//'| sed 's/[[:blank:]]//g'|sort -g|tail -1|awk '{print $1/1000}')
	fi

	WriteBw=$(echo -e $file_name |awk -f JSON.awk|grep '"write","bw"'| sed 's/.*]//'| sed 's/[[:blank:]]//g'| paste -sd+ - | ${bc_cmd})
	IFS='-' read -r -a array <<< "$file_name"
	TestType=${array[2]}
	BlockSize=${array[3]}
	Threads=$(echo "${array[4]}"| sed "s/td\.json//")
	TotalIOPS=$(echo $ReadIOPS $WriteIOPS	| awk '{printf "%d\n", $1+$2}')
	echo "$Iteration,$TestType,$BlockSize,$Threads,$Jobs,$TotalIOPS,$ReadIOPS,$MaxOfReadMeanLatency,$ReadMaxLatency,$ReadBw,$WriteIOPS,$MaxOfWriteMeanLatency,$WriteMaxLatency,$WriteBw" >> $csv_file_tmp
	((count++))
done

echo ",Max IOPS of each mode," >> $csv_file
echo ",Test Mode,Max IOPS (BSize-iodepth)," >> $csv_file
modes='randread randwrite read write' 
for testmode in $modes 
do
	max_iops=$(cat $csv_file_tmp | grep ",$testmode" | awk '{split($0,arr,","); print arr[6]}'| sort -g|tail -1)
	max_bs=$(cat $csv_file_tmp | grep ",$testmode"| grep ",$max_iops" | awk '{split($0,arr,","); print arr[3]}')
	max_iodepth=$(cat $csv_file_tmp | grep ",$testmode"| grep ",$max_iops" | awk '{split($0,arr,","); print arr[4]}')
	if  [ "x$max_iops" != "x" ]
	then
		echo ",$testmode,$max_iops ($max_bs-$max_iodepth)," >> $csv_file
	fi
done

echo "" >> $csv_file
echo ",Max IOPS of each BlockSize," >> $csv_file
modes='randread randwrite read write'
block_sizes='1K 2K 4K 8K 16K 32K 64K 128K 256K 512K 1024K 2048K'
echo ",Test Mode,Block Size,iodepth,Max IOPS (BSize-iodepth)," >> $csv_file
for testmode in $modes 
do
	for block in $block_sizes 
	do
		max_iops=$(cat $csv_file_tmp | grep ",$testmode" | grep ",$block" | awk '{split($0,arr,","); print arr[6]}'| sort -g|tail -1)

		max_bs=$(cat $csv_file_tmp | grep ",$testmode"| grep ",$block"| grep ",$max_iops" | awk '{split($0,arr,","); print arr[3]}')
		max_iodepth=$(cat $csv_file_tmp | grep ",$testmode"| grep ",$block"| grep ",$max_iops" | awk '{split($0,arr,","); print arr[4]}')

		if  [ "x$max_iops" != "x" ]
		then
		echo ",$testmode,$block,$iodepth,$max_iops ($max_bs-$max_iodepth)," >> $csv_file
		fi
	done
done
echo "" >> $csv_file
cat $csv_file_tmp >> $csv_file
rm -rf $csv_file_tmp
echo "Parsing completed!" 
exit 0