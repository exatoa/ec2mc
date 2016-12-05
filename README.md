EC2MC
================
### 개요
	* 다수의 계정에 EC2 Instance들을 생성하고 삭제하는 기능을 제공하는 라이브러리
	* Python 2.7 기반에서 작성된 코드.
	* EC2Controller.py : EC2 Instance들을 제어하는 method들을 제공
	* AmazonUtils.py : EC2Controller를 위해 Amazon boto라이브러리를 wrapping 하여 가공
	* AmazonInfo.py : EC2 Instance를 제어하는데 필요한 기본값들을 보관
	                  ex) AMI Image ID, Region ID, Instance Type ID 등.
	* EC2Controller는 상속을 통해서 EC2 Instance에 사용자가 원하는 작업을 수행하도록 지원
	* 이를 위해 Sample 코드로써, EC2 Instance들을 Proxy 서버로 생성하는 코드를 함께 제공
	
### Library dependency
	* boto3 : EC2MC의 동작을 위해 필요한 라이브러리 (amazon_boto)
	* botocore : EC2MC의 동작을 위해 필요한 라이브러리 (amazon_boto)
	* fabric : 코드로 원격지 컴퓨터에 SSH를 통해 명령어를 수행하는 라이브러리
	* Flask : Web Server library (설정파일 다운로드를 위해서 사용)

	* 설치 : pip install boto3 botocore fabric Flask



Sample (AWS Proxy server group manger)
---------------------------------------
	* EC2MC의 응용 예를 보여주기 위한 코드들
	* sample 폴더와 AWSProxy.py가 해당 코드들이다.


### Sample Code를 위한 준비작업
	1. sample폴더로 이동하여 python WebServer.py를 실행
		* python WebServer.py -d ./ -p 80
		* 그러면 현재 자신의 컴퓨터가 80포트로 웹서버가 된다. (서비스폴더 : 현재폴더)
		* 만약 자신의 공인IP가 5.5.5.5라고 하면 http://5.5.5.5:80이 서버 주소가 된다.

	2. 루트폴더의 AWSProxy.py의 설정에 squidSettingURL변수의 값을 수정
		* squidSettingURL = u'http://5.5.5.5:80/squid.conf'

	3.  AWSsettins.py 파일에서 Amazon 계정의 Access key 값을 설정
		* Amazon AWS Login > Management Console > Security Credentials
		* Access Key > Create new Access key
		* access_key와 secret_access_key를 확인하여 AWSsettins.py의 ACCOUNTS에 기록
		
	4. AWSsettins.py 파일에서 OUTPUT_PATH 설정
		* 로그인에 필요한 key pair나 결과들이 출력될 폴더 지정

### Sample Code 실행
	* python AWSProxy.py -s create -n 2 -t 5
		+ Amazon 계정에 서버를 생성
		+ 각 계정에 2개의 instance를 생성
		+ 5개의 thread를 이용해서 작업 수행

	* python AWSProxy.py -s local_status
		+ 현재 생성된 instance정보들을 보여줌 (local의 정보 이용)

	* python AWSProxy.py -s remote_status
		+ 현재 생성된 instance정보들을 보여줌 (account에서 정보를 조회)

	* python AWSProxy.py -s clear
		+ 생성된 모든 Instance들을 제거함
		+ local에 저장된 정보를 바탕으로 제거하므로 local에 저장된 정보가 손실되면 에러

	* python AWSProxy.py -s clear_force
		+ Amazon 계정에 생성된 Instance들을 조사한 후에 프로그램에서 생성한 Instace들을 제거

	* python AWSProxy.py -l watch
		+ 각 Instace에 요청된 request의 수치를 볼 수 있음. (매 15초마다 갱신됨)

	* python AWSProxy.py -l clear
		+ 각 Instance에 저장된 log들을 지우고 초기화 함 


주의사항
---------------------------------------
	* 기본적으로 Amazon Library인 boto3에 의존하고 있어, Library변경시 문제가 발생될 수 있음.
	* AmazonInfo.py에 기록된 정보들은 Amazon에서 코드를 변경하게 되면 문제가 발생될 수 있음.
