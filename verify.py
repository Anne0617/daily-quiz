import urllib.request, json
r = urllib.request.urlopen("http://localhost:8080/quiz?day=1")
html = r.read().decode("utf-8")
print(f"Quiz page: {len(html)} bytes")
print("OK: btn-submit found" if "btn-submit" in html else "FAIL")
print("OK: questions found" if "question-card" in html else "FAIL")

data = json.dumps({"name":"Test","department":"Test","day_seq":1,"answers":["B","C","C","A","C"]}).encode()
req = urllib.request.Request("http://localhost:8080/api/submit", data=data, method="POST")
req.add_header("Content-Type","application/json")
resp = json.loads(urllib.request.urlopen(req).read())
print(f"Submit result: {resp['score']}/5")
if resp["score"] == 5:
    print("ALL TESTS PASSED")
else:
    print(f"Expected 5, got {resp['score']}")
