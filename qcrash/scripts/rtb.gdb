set $a=msm_rtb.enabled
set $start=msm_rtb.rtb
set $c=msm_rtb.nentries
set $d=msm_rtb.initialized
set $e=msm_rtb.filter
set $f=&msm_rtb_idx_cpu
set $step=msm_rtb.step_size*0x20
set $end=(unsigned long int)$start+msm_rtb.size

define rtb
    if $d!=1
        printf "rtb not initialzed\r\n"
    end
    if $a!=1
        printf "rtb not enabled \r\n"
    end
    if $argc != 2
        printf "wrong, please input cpu number and number\r\n"
    else
        set $offset=__per_cpu_offset[$arg0]
        set $last=*((unsigned long int)$offset+(unsigned long int)$f)
        set $last=$last%$c
        set $addr=$last*0x20+(unsigned long int)$start
        set $stepoff=0x20*$arg0
        set $first=$addr
        set $cnt=0
        printf "%lx %lx %lx\r\n", $addr,  $start, $end
        set $next=$addr-$step
        if $next<$start
            $next=(unsigned long int)$end-(unsigned long int)$step+(unsigned int)$stepoff
        end
        
        while $cnt<$arg1
            set $idx=((struct msm_rtb_layout*)$next)->idx
            set $time=((struct msm_rtb_layout*)$next)->timestamp
            set $caller=((struct msm_rtb_layout*)$next)->caller
            set $data=((struct msm_rtb_layout*)$next)->data
            set $type=((struct msm_rtb_layout*)$next)->log_type
            printf "%x:%lx %lx %lx  ", $idx, $time, $data, $caller
            print (enum logk_event_type)$type
            set $next=$next-$step
            set $cnt=$cnt+1
            if $next<$start
                set $next=(unsigned long int)$end-(unsigned long int)$step+(unsigned int)$stepoff
            end
        end
    end
end

