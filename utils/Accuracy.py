from jamo import h2j, j2hcj
chosung_list = set(['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'])

class Accuracy:
  # 문자열을 한 글자씩 분리
  def __splitLetter(self, target: str) -> list:
    return list(target)

  # 문자열을 초성, 종성, 중성으로 분리 및 겹자음, 겹모음을 분리
  def __convertJamo(self, target: str) -> list:
    _list = []
    for word in target:
      letters = self.__splitLetter(j2hcj(h2j(word)))
      for letter in letters:
        if(letter == "ㅆ"):
           _list.append("ㅅ")
        elif(letter == "ㅃ"):
           _list.append("ㅂ")
        elif(letter == "ㄲ"):
           _list.append("ㄱ")
        elif(letter == "ㄸ"):
           _list.append("ㄷ")
        elif(letter == "ㅉ"):
           _list.append("ㅈ")
        elif(letter == "ㅢ"):
           _list.append("ㅡ")
           _list.append("ㅣ")
        elif(letter == "ㅟ"):
           _list.append("ㅜ")
           _list.append("ㅣ")
        elif(letter == "ㅒ"):
           _list.append("ㅐ")
        else:
          _list.append(letter)
    return _list

  # 검사할 문자열과, 원본 문자열을 합침
  # set() 을 통해 중복된 문자열을 제거
  def __extends(self, target: str, original: str) -> set:
    letter = self.__splitLetter(target)
    jamo = self.__convertJamo(letter)

    orignal_letter = self.__splitLetter(original)
    original_jamo = self.__convertJamo(orignal_letter)

    return [set(jamo), set(original_jamo)]

  # 비속어의 감지 기준은 다음과 같음
  # ---
  # 겹치지 않는 모음의 수가 1개 이하
  # 겹치지 않는 자음의 수가 0개

  # Usage: self.compare("씨발", "시발")
  # Returns: {'result': True, 'is_overlap_chosung': [], 'not_overlap': [], 'reverse_overlap': []}
  def compare(self, target: str, original: str) -> dict:
    result = self.__extends(target, original)
    not_overlap = list(result[0].difference(result[1]))
    reverse_overlap = list(result[1].difference(result[0]))
    is_overlap_chosung = list(set(not_overlap).intersection(chosung_list))
    
    __object = dict()
    if(len(is_overlap_chosung) == 0 and len(not_overlap) <= 1 and len(reverse_overlap) <= 1):
      __object["result"] = True
      __object["is_overlap_chosung"] = is_overlap_chosung
      __object["not_overlap"] = not_overlap
      __object["reverse_overlap"] = reverse_overlap
    else:
      __object["result"] = False

    return __object
