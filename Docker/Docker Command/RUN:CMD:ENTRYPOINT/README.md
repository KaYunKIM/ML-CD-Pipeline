#### RUN

- Shell command 실행과 같이 이미지 빌드 과정에서 필요한 커맨드 실행하기 위해 사용
- 보통 이미지 위에 패키지를 설치하고, 새로운 레이어 생성(RUN 명령어 실행할 때 마다)할 때 사용



#### CMD

- default 명령어나 파라미터 설정에 사용
- docker run 실행 시 별도의 command 주지 않으면, CMD 명령어가 default로 실행됨
- docker run 실행 시 command 명령어(ex. echo)가 있다면, CMD 명령어는 무시됨(덮어쓰기)
- 즉, docker container 실행할 때 사용할 default 명령어를 설정함
- 여러개의 CMD 중 가장 마지막 CMD 1개만 실행 됨



#### ENTRYPOINT

- docker run 실행 시 수행하는 명령어로 container를 실행할 수 있게 설정 함
- CMD와의 차이점으로는 container 실행 시 반드시 ENTRYPOINT에서 지정한 명령만 수행함
  - docker run 명령어로 지정한 인자값으로 변경 불가
  - 따라서 container를 띄울 때 변경되지 않을 명령어는 ENTRYPOINT를 사용할 것!



위 세가지 모두 두가지 명령어 방식을 따름

- `exec form`(Preferred): RUN/CMD/ENTRYPOINT ["executable", "param1", "param2"]
- `shell form`: RUN/CMD/ENTRYPOINT command param1 param2



RUN/CMD/ENTRYPOINT 명령어에 ENV 변수 전달하기

- 위 Dockerfile 예제에서는 exec form에서 ENV 변수가 전달이 안 되어 shell form(변수 대체 가능)으로 사용함

  ```bash
  ENV MODEL_VERSION="${MODEL_NAME}_${TIMESTAMP}"
  
  # 컨테이너 실행
  CMD python3 app.py --aws-conf=aws --model-conf=model --model-version=$MODEL_VERSION
  ```

- 이를 exec form으로 실행하기 위해서는 shell로 echo 명령어를 사용하여 실행 할 수 있음

  ```bash
  ENV MODEL_VERSION="${MODEL_NAME}_${TIMESTAMP}"
  
  # 컨테이너 실행
  CMD ["python3", "app.py", "--aws-conf=aws", "--model-conf=model", "echo --model-version=$MODEL_VERSION"]
  ```