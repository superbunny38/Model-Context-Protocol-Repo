# MCP로 진짜 비서 된 Claude! 로컬 정리 + 드라이브 자동화 (코드 무료 제공)

Ref:
- https://www.youtube.com/watch?v=Pt1tEBCLiCc
- https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem


Prompts:
1) /Users/chaeeunryu/Desktop/2025Spring/ADL/Ref에 있는 논문 리스트를 보여줘
2) 해당 pdf 파일 논문들의 Abstract를 읽고 그 내용을 바탕으로 아래와 같이 파일 명을 변경해줘.
- 파일 명 포맷: 'YYYY-논문제목-논문 주 저자-인용 횟수'
- YYYY는 논문의 발행연도를 기입해줘
- 논문 주저자는 첫 번째 저자를 기입해줘
- 인용횟수는 semanticscholar.org를 검색해서 citation count를 찾아서 기입해줘