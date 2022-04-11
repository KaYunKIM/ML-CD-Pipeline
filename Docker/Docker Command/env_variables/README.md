### 변수 사용

`$`

- 변수 사용시에는 "=" 앞 뒤로 공백 없이 입력해야 한다.

- 선언한 변수를 사용하기 위해서는 ${변수이름}/ $변수이름 으로 표기

  ```bash
  ENV MODEL_NAME="groobee_search"
  
  ENV MODEL_VERSION="${MODEL_NAME}_${TIMESTAMP}"
  ```

``(백틱)`

Template literals

- JavaScript에서 문자열을 입력하는 방식
- 내장된 표현식을 허용하는 문자열 리터럴
- 런타임 시점에 일반 javascript 문자열로 처리 및 변환
- 백틱(`)은 내부 명령어의 실행 결과를 스트링으로 반환

```bash
TIMESTAMP=`date +%y%m%d%H%M`
# TIMESTAMP=2106251525
```

