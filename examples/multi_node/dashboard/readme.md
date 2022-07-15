You also need to setup Grafana according to [this](https://grafana.com/tutorials/run-grafana-behind-a-proxy/)  
You can open the container like:  
´docker exec -it -u 0 dashboard bash´  
then install an editor:  
`apt update && apt install vim`  
then edit /etc/grafana/grafana.ini according to the link above:  
`vim /etc/grafana/grafana.ini`  
restart the container with  
`docker restart dashboard`