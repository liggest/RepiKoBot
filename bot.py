from repiko import app

if __name__ =='__main__':
    import uvicorn
    uvicorn.run("repiko:app",host='0.0.0.0',port=8080,debug=True)