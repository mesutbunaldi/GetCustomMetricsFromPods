import os
import sys
import subprocess
import json
import datetime
import time
import yaml
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.exposition import basic_auth_handler




pushgateway_url = 'http://localhost:9091'



kubectl_command = "kubectl get pods -o custom-columns=:metadata.name"
completed_process = subprocess.run(kubectl_command, shell=True, stdout=subprocess.PIPE, text=True)
if completed_process.returncode == 0:
    pod_names_output = completed_process.stdout
    pod_names = pod_names_output.splitlines()
else:
    print("Error running kubectl command.")

for pod in pod_names:
    if pod != "":
        kubectl_command = "kubectl get pod "+ str(pod) +" -o yaml"
        completed_process = subprocess.run(kubectl_command, shell=True, stdout=subprocess.PIPE, text=True)
        if completed_process.returncode == 0:
            pod_info = completed_process.stdout
            pod_info_dict = yaml.safe_load(pod_info)
            print("Name of Pod : ",pod_info_dict['metadata']['name'])
            registry = CollectorRegistry()
            # create job_name for pushgateway
            job_name = pod_info_dict['metadata']['namespace']

           #create a gauge metric (pod_name_metric) for pod name
            # pod_name_metric = Gauge('pod_name', 'pod_name', registry=registry)
            
            
            pod_name = pod_info_dict['metadata']['name']

            job_name = job_name +"_"+ pod_name
            # remove - and . from pod name
            pod_name = pod_name.replace("-","_")
            # pod_name_metric.set(pod_info_dict['metadata']['name'])

            creation_time = pod_info_dict['metadata']['creationTimestamp'].split("T")[1].split(".")[0].split("Z")[0]
           # print("Creation TimeStamp of Pod : ", creation_time)
            conditions = pod_info_dict.get("status", {}).get("conditions", [])
            podScheduled, initialized, ready, containersReady = (0, 0, 0, 0)
            for condition in conditions:
                condition_type = condition.get("type")
                last_transition_time = condition.get("lastTransitionTime")
                
                if condition_type and last_transition_time:
                    last_transition_time= datetime.datetime.strptime(last_transition_time.split("T")[1].split(".")[0].split("Z")[0], '%H:%M:%S')
                    formatted_time = last_transition_time.strftime("%H:%M:%S")
                    #print(condition_type, ":",formatted_time)
                    if condition_type == "Initialized":
                        initialized = formatted_time
                    elif condition_type == "PodScheduled":
                        podScheduled = formatted_time
                    elif condition_type == "Ready":
                        ready = formatted_time
                    elif condition_type == "ContainersReady":
                        containersReady = formatted_time
            #print("Creation Time :",creation_time," PodScheduled : ",podScheduled,"Initialized : ",initialized," ContainersReady : ",containersReady, " Ready : ",ready)
            total_ready_time = datetime.datetime.strptime(ready, '%H:%M:%S') - datetime.datetime.strptime(creation_time, '%H:%M:%S')
            schedule_time = datetime.datetime.strptime(podScheduled, '%H:%M:%S') - datetime.datetime.strptime(creation_time, '%H:%M:%S')
            initialize_time = datetime.datetime.strptime(initialized, '%H:%M:%S') - datetime.datetime.strptime(podScheduled, '%H:%M:%S')
            containers_ready_time = datetime.datetime.strptime(containersReady, '%H:%M:%S') - datetime.datetime.strptime(initialized, '%H:%M:%S')
            ready_time = datetime.datetime.strptime(ready, '%H:%M:%S') - datetime.datetime.strptime(containersReady, '%H:%M:%S')
            
            # create a gauge metric(schedule_time_metric) for schedule time of pod
            schedule_time_metric = Gauge(pod_name+'_schedule_time', 'sec', registry=registry)
            schedule_time_metric.set(schedule_time.total_seconds())

            # create a gauge metric(initialize_time_metric) for initialize time of pod
            initialize_time_metric = Gauge(pod_name+'_initialize_time', 'sec', registry=registry)
            initialize_time_metric.set(initialize_time.total_seconds())

            # create a gauge metric(containers_ready_time_metric) for containers ready time of pod
            containers_ready_time_metric = Gauge(pod_name+'_containers_ready_time', 'sec', registry=registry)
            containers_ready_time_metric.set(containers_ready_time.total_seconds())

            # create a gauge metric(ready_time_metric) for ready time of pod
            ready_time_metric = Gauge(pod_name+'_ready_time', 'sec', registry=registry)
            ready_time_metric.set(ready_time.total_seconds())

            # create a gauge metric(total_ready_time_metric) for total ready time of pod
            total_ready_time_metric = Gauge(pod_name+'_total_ready_time', 'sec', registry=registry)
            total_ready_time_metric.set(total_ready_time.total_seconds())





            print("Schedule Time : ",schedule_time.total_seconds()," seconds")
            print("Initialize Time : ",initialize_time.total_seconds()," seconds")
            print("Containers Ready Time : ",containers_ready_time.total_seconds()," seconds")
            print("Ready Time : ",ready_time.total_seconds()," seconds")     
            print("Total Ready Time : ",total_ready_time.total_seconds()," seconds")
              
                
            init_containers = pod_info_dict.get("status", {}).get("initContainerStatuses", [])
            for init_container in init_containers:
                finished_at = init_container['state']['terminated']['finishedAt'].split("T")[1].split(".")[0].split("Z")[0]
                started_at = init_container['state']['terminated']['startedAt'].split("T")[1].split(".")[0].split("Z")[0]
                exec_time_interval= datetime.datetime.strptime(finished_at, '%H:%M:%S') - datetime.datetime.strptime(started_at, '%H:%M:%S')
                exec_time_interval = exec_time_interval.total_seconds()
                print(init_container['name']," execution times : ", exec_time_interval," seconds")
                # create a gauge metric(init_container_metric) for init container execution time
                init_container_metric = Gauge(pod_name+'_init_container_'+init_container['name'].replace("-","_")+'_exec_time', 'sec', registry=registry)  
                init_container_metric.set(exec_time_interval)
                #

          

           
            # print kubectl describe pod pod and get events only reason Pulled
            kubectl_command = "kubectl describe pod "+ str(pod) +" | grep -i pulled  | awk '{print  $8,$9,$10}'"
            completed_process = subprocess.run(kubectl_command, shell=True, stdout=subprocess.PIPE, text=True)
            if completed_process.returncode == 0:
                pod_pulled_info = completed_process.stdout
                # print((pod_pulled_info))
                image_pulled_times = pod_pulled_info.splitlines()
                for image_pulled_time in image_pulled_times:
                    
                    if image_pulled_time.find("already present on")==-1:
                        #print(image_pulled_time)
                        #split image name and pulled time
                        image_name = image_pulled_time.split()[0]
                        pulled_time = image_pulled_time.split()[2]
                        #print("RAW   : ",image_name," : ",pulled_time)
                        # check if pulled time include ms
                        if pulled_time.find("ms")!=-1:
                            # remove ms from pulled time
                            pulled_time = pulled_time.split("ms")[0]
                            # convert pulled time to seconds
                            pulled_time = float(pulled_time)/1000
                        # else if pulled time include s
                        elif pulled_time.find("s")!=-1 and pulled_time.find("m")==-1:
                            # remove s from pulled time
                            pulled_time = pulled_time.split("s")[0]
                            # convert pulled time to seconds
                            pulled_time = float(pulled_time)
                        elif pulled_time.find("m")!=-1 and pulled_time.find("s")!=-1:
                            # remove m from pulled time
                            pulled_time = pulled_time.split("m")[0]
                            # convert pulled time to seconds
                            pulled_time = float(pulled_time)*60

                       
                        # change pulled time float 2 decimal
                        pulled_time = "{:.2f}".format(pulled_time)
                        print("Pulled : ",image_name," : ",pulled_time," seconds")
                #print(pod_pulled_info.splitlines()[0].split()[0],":",pod_pulled_info.splitlines()[0].split()[4:4])

            # print only inside of pharantesis of kubectl describe pod pod and get events only reason Pulled
           


              
                push_to_gateway(pushgateway_url, job=job_name, registry=registry)
            print("----------------------------------------------------")
        else:
            print("Error running kubectl command.")