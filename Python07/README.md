# MCP로 진짜 비서 된 Claude! 로컬 정리 + 드라이브 자동화 (코드 무료 제공)

Ref:
- https://www.youtube.com/watch?v=Pt1tEBCLiCc
- https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- https://github.com/modelcontextprotocol/servers/tree/main/src/gdrive


Prompts:
1) /Users/chaeeunryu/Desktop/2025Spring/ADL/Ref에 있는 논문 리스트를 보여줘
2) 해당 pdf 파일 논문들의 Abstract를 읽고 그 내용을 바탕으로 아래와 같이 파일 명을 변경해줘.
- 파일 명 포맷: 'YYYY-논문제목-논문 주 저자-인용 횟수'
- YYYY는 논문의 발행연도를 기입해줘
- 논문 주저자는 첫 번째 저자를 기입해줘
- 인용횟수는 semanticscholar.org를 검색해서 citation count를 찾아서 기입해줘


## Server local로 활용
npm install 하면 package.json이 다운 받아짐 

claude config 수정시:
- command에서 npx 삭제
- args에서 "@modelcontextprotocol/server-gdrive" 삭제
- command에 /Users/chaeeunryu/Downloads/servers-main/node_modules/.bin/mcp-server-gdrive로 대체 (실행파일임. windows면 .cmd 붙여야함)


Prompts:
구글 드라이브에서 "NaiveStudentModelTraining.ipynb" 문서를 찾아줘

새로운 기능 개발하고 싶으면 index.ts 고치면 됨
