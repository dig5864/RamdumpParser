
define lpmstatus
    set $a=lpm_root_node->child.next
    p ((struct lpm_cluster*)$a)->cluster_name
    set $b=((struct lpm_cluster*)$a)->stats->time_stats
    p $b[0]
    p $b[1]
    p $b[2]
    set $a=lpm_root_node->child.prev
    p ((struct lpm_cluster*)$a)->cluster_name
    set $b=((struct lpm_cluster*)$a)->stats->time_stats
    p $b[0]
    p $b[1]
    p $b[2]
end

define lpmevents
    if $argc != 1
        printf "wrong, please input number\r\n"
    end
    if $arg0>256
        printf "too large, max is 256\r\n"
    else
        set $index=255
        set $lastt=0x7fffffffffffffff
        while $index>0
            set $t=(((struct lpm_debug*)lpm_debug)[$index]).time
            if $t>$lastt
               loop_break 
            else
                set $index=$index-1
                set $lastt=$t
            end
        end
        printf "Start: %d\r\n", $index
        set $a=0
        while $a<$arg0
            set $a1=(((struct lpm_debug*)lpm_debug)[$index]).arg1
            set $a2=(((struct lpm_debug*)lpm_debug)[$index]).arg2
            set $a3=(((struct lpm_debug*)lpm_debug)[$index]).arg3
            set $a4=(((struct lpm_debug*)lpm_debug)[$index]).arg4
            set $cpu=(((struct lpm_debug*)lpm_debug)[$index]).cpu
            set $evt=(enum debug_event)((((struct lpm_debug*)lpm_debug)[$index]).evt)
            set $t=(((struct lpm_debug*)lpm_debug)[$index]).time
            printf "%d time:%ld CPU:%d arg1:%8x arg2:%8x, arg3:%8x arg4:%8x Evt: ", $index, $t, $cpu,$a1, $a2, $a3, $a4
            p $evt
            set $a=$a+1
            if $index==0
                set $index=255
            else
                set $index=$index-1
            end
        end
    end
end
