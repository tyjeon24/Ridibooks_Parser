import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

PUBLISHER_REGEX_PATTERN = r"(?<=\>).*?(?=\<\/a\> 출판)"
PUBLISHING_DATE_SELECTOR = "li.Header_Metadata_Item.book_info.published_date_info > ul > li"
TITLE_REGEX_PATTERN = r".*?(?= \| )"
WRITER_REGEX_PATTERN = r"(?<= \| ).*?(?= 저)"

class RidibooksParser():
	def __init__(self, file_list, metadata = {}):
		self.custom_metadata = metadata
		self.metadata = {}
		self.contents = []
		self.df = pd.DataFrame({'날짜': [],
		                   '저자': [],
		                   '제목': [],
		                   '페이지': [],
		                   '태그': [],
		                   '내용': [],
		                   '코멘트': [],
		                   '출판사': [],
		                   '출판연도': [],
		                  })
		self.parse_ridibooks_text()

	def parse_ridibooks_text(self):
		for file in file_list:
			if ".py" in file:
				continue

			self.read_contents(file)
			self.set_metadata()
			time = re.search(r"%d+(?=\.txt)", file)
			if time != None:
				print(time)

			self.parse_contents()
			self.append_data()
		print(self.df)
		self.df.to_excel("output.xlsx")


	def read_contents(self, file):
		with open(file, mode="r", encoding="utf-8") as f:
			self.contents = [line for line in f.readlines() if line!= ""]

	def set_metadata(self):
		self.metadata = {
			"날짜" : str(datetime.now()),
			"저자" : "",
			"제목" : "",
			"페이지" : "",
			"태그" : "",
			"내용" : "",
			"코멘트" : "",
			"출판사" : "",
			"출판연도" : ""
		}

		for key, value in self.custom_metadata.items():
			self.metadata[key] = value
		self.find_metadata()

	def find_metadata(self):
		metadata = {"출판연도" : ""}
		content = self.contents.pop()
		url = re.search(r"https.*", content).group()

		if "리디북스에서 자세히 보기" in content:
			self.contents.pop()
			content = self.contents.pop()
			metadata["제목"] = re.search(TITLE_REGEX_PATTERN, content).group().strip()
			if metadata["제목"] != self.metadata["제목"] and self.metadata["제목"] != "":
				print("오류 발생 : 유저 입력 데이터와 책 제목이 다릅니다. 프로그램을 종료합니다.")
				exit()

		else: # 리디북스에서 구매한 책이 아닌 경우
			self.contents.pop()
			metadata["제목"] = self.contents.pop().strip()


		is_metadata_in_database = (self.df[self.df["제목"] == metadata["제목"]].count(axis=0)["제목"] > 0)
		if is_metadata_in_database:
			print("데이터베이스에서 데이터를 가져옵니다.")
			temp_df = self.df[self.df["제목"] == metadata["제목"]]
			metadata["저자"] = temp_df["저자"].values[0]
			metadata["출판사"] = temp_df["출판사"].values[0]
			metadata["출판연도"] = temp_df["출판연도"].values[0]


		elif url != "https://ridibooks.com": # 리디북스에서 구매한 책일 경우
			metadata["저자"] = re.search(WRITER_REGEX_PATTERN, content).group().strip()

			html = requests.get(url).text
			metadata["출판사"] = re.search(PUBLISHER_REGEX_PATTERN, html).group()

			for date in BeautifulSoup(html, "html.parser").select(PUBLISHING_DATE_SELECTOR):
				metadata["출판연도"] = "{}\n{}".format(metadata["출판연도"], date.text.replace("\n","").strip()).strip()

			print("사이트에서 메타데이터를 찾았습니다.\n출판사 : {}, 출판연도 : {}".format(metadata["출판사"], metadata["출판연도"]))

		for key, value in metadata.items():
			if self.metadata[key] == "":
				self.metadata[key] = value

	def parse_contents(self):
		latest_keyword = "내용"
		for line in self.contents:
			for keyword in ["태그", "코멘트", "페이지"]:
				pattern = r"{} ?: ?".format(keyword)

				is_specific_keyword_in_line = (re.search(pattern, line) != None)
				if is_specific_keyword_in_line:
					latest_keyword = keyword

			self.metadata[latest_keyword] += "\n" + line
			self.metadata[latest_keyword] = self.metadata[latest_keyword].strip()
	
	def append_data(self):
		self.df.loc[len(self.df)] = self.metadata

file_list = os.listdir()
metadata = {
			"저자" : "크리스 아벨론",
			"제목" : "Planescape Torment(플레인스케이프 토먼트) 대사집",
			"출판사" : "Black Isle Studios",
			"출판연도" : "1999"
			}
RidibooksParser(file_list)