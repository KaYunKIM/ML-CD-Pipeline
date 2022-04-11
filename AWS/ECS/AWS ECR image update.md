How to update ECR images in ECS service



1. AWS CLI command(using the same image tag name)

Use CodeBuild to push the new image. 

Make sure the task definition is using the "latest" tag. You'll need to force the deployment of the task definition to pick the new image.

```
aws ecs update-service --cluster <<cluster-name>> --service <<service-name>> --force-new-deployment --region <<region>>
```

=> But, 같은 이름의 태그 이미지를 사용한다면 롤백의 어려움이 있음



2. Use CodePipeline to update ECS. 

It will automatically generate a new task definition revision with the new image and deploy it.



#### 이미지 태그는 꼭 latest로 해줘야 최신 버전으로 업데이트 가능!

```
STOPPED (CannotPullContainerError: inspect image has been retried 1 time(s): failed to resolve ref "262429377270.dkr.ecr.ap-northeast-2.amazonaws.com/keyword-dev:latest": 262429377270.dkr.ecr.ap-northeast-2.amazonaws.com/keyword-dev:latest: not found)
```

