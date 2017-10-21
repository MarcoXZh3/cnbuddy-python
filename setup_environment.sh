# Install basic packages for steem-python development
sudo add-apt-repository ppa:jonathonf/python-3.6
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev libffi-dev python3.6 python3-pip \
                        mysql-server mysql-client libmysqlclient-dev
sudo mysql_secure_installation
sudo service mysql stop && sudo /etc/init.d/apparmor reload && sudo service mysql start
sudo pip3 install -U pip virtualenv             # steem must be installed system-wide, not within virtualenv
virtualenv -p python3.6 temp                    # A temporay python3.6 virtualenv for installing dependencies
source temp/bin/activate
    pip install steem                           # This hans for a while at the beginning, and will finally fail
    deactivate
rm -rf temp                                     # Never use it again
sudo pip3 install -U steem                      # Now it works, otherwise repeat the "temp" installation
virtualenv -p python3 --system-site-packages python3    # Steem is found only in **python3.5**, NOT python3.6
source python3/bin/activate
    pip install piston-lib natsort mysql-connector-python-rf apscheduler PyMongo SQLAlchemy django mysqlclient
