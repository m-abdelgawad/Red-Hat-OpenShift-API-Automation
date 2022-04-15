# Program Name	: Red Hat OpenShift API Automation
# Version       : 1.0
# Date          : 26 October 2021
# Author     	: Mohamed Abdel-Gawad Ibrahim
# Email         : muhammadabdelgawwad@gmail.com


# Import essentials packages
import requests
from kubernetes import client
from openshift.dynamic import DynamicClient
from openshift.helper.userpassauth import OCPLoginConfiguration
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# disable insecure requests warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class OpenShift:
	"""Connect and query RedHat Openshift
	"""
	
	def __init__(self, host, port, username, password, tag):
		"""Instantiate OpenShift object

		Args:
			host (str): host of RedHat OpenShift
			port (str): Port of OpenShift
			username (str): Username of Openshift account
			password (str): Password of Openshift account
			tag (str): A tag to mark the object with a unique name
		"""
		
		# build API Host URL
		self.client = None
		API_host = '{}:{}'.format(host, port)
		
		# Set log in configurations
		self.config = OCPLoginConfiguration(ocp_username=username, ocp_password=password)
		
		# Set Host
		self.config.host = API_host
		
		# disable verifying SSL
		self.config.verify_ssl = False
		
		# Set tag
		self.tag = tag
	
	def get_auth_token(self, is_print):
		"""Get Authorization token and its expiration time in hours

		Args:
			is_print (bool): A boolean to indicate if we should print the
				token or not.
				The token in the following format:
				{'authorization': 'Bearer sha256~tUJonJs-3kD-wqKis0ySxaehGKrpQspv_NIqx64DKVs'
				}
		"""
		
		# Get token
		self.config.get_token()
		
		# Gen the API Key
		token_dict = self.config.api_key
		
		# Get the lifetime of the API key in seconds.
		# Usually it equals 24 hours.
		expire_hrs = self.config.api_key_expires
		
		# Check if we should print the token or not
		if is_print:
			# Print Token and its expiration period
			print('Auth token: {}'.format(token_dict))
			print('Token expires: {}'.format(expire_hrs))
	
	def create_client(self):
		"""Create a client to communicate with Openshift
		"""
		
		k8s_client = client.ApiClient(self.config)
		self.client = DynamicClient(k8s_client)
	
	def get_pods_count(self, service_name, namespace):
		"""Get the current running pods for a specific service in a namespace

		Args:
			service_name (str): The service name that's running on Openshift and
				we want to get the count of its current running pods.
			namespace (str): The namespace that contains the service_name

		Returns:
			[dict]: a dictionary with two keys:
				'service' --> Service name.
				'pods_count' --> The number of running pods.
		"""
		
		# Connect to API: v1\Pod
		v1_pod = self.client.resources.get(api_version='v1', kind='Pod')
		
		# Get the results for the namespace variable
		v1_results = v1_pod.get(namespace=namespace)
		
		# Extract all running pods names of the service_name into a list
		pods_list = [pod.metadata.name for pod in v1_results['items'] if service_name in pod.metadata.name]
		
		# Calculate the number of running pods
		pods_count = len(pods_list)
		
		# Return the results into a dictionary
		return {service_name: {'running': pods_count}}
	
	def get_service_limits(self, service_name, namespace, results_dict):
		"""Get the configured limits - max & min pods - of a service in a
		namespace.

		Args:
			service_name (str): The service name that's running on Openshift and
				we want to get the count of its current running pods.
			namespace (str): The namespace that contains the service_name
			results_dict (dict): a dictionary to store the results inside it,
				then return it.

		Returns:
			results_dict[dict]: The results dictionary with two more keys:
				'min_pods' --> The minimum configured pods.
				'max_pods' --> The maximum configured pods.
		"""
		
		# Connect to API: v2beta2\HorizontalPodAutoscaler
		v2_configs = self.client.resources.get(
			api_version='v2beta2',
			kind='HorizontalPodAutoscaler'
		)
		
		# Get the results for the namespace variable
		v2_results = v2_configs.get(namespace=namespace)
		
		# Extract the minimum configured pods for the service_name
		results_dict[service_name]['min'] = [item.spec.minReplicas for item in \
		                                     v2_results['items'] if service_name in item.metadata.name][0]
		
		# Extract the minimum configured pods for the service_name
		results_dict[service_name]['max'] = [item.spec.maxReplicas for item in \
		                                     v2_results['items'] if service_name in item.metadata.name][0]
		
		# Return the results into a dictionary
		return results_dict
