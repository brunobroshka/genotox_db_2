from myapp.views import startclean_DeepAmes, query_DeepAmes

def test_startclean():
    df = startclean_DeepAmes()
    if df.empty:
        print("startclean_DeepAmes failed: DataFrame is empty")
    else:
        print("startclean_DeepAmes succeeded:")
        print(df.head())

def test_query():
    result = query_DeepAmes("50-00-0")  # Replace with a valid CAS number
    if result is not None:
        print("Query succeeded:")
        print(result)
    else:
        print("Query failed: No data found for the given CAS_RN")

if __name__ == "__main__":
    test_startclean()
    test_query()
