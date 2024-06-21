import subprocess
import time
from pywinauto.application import Application
from win32con import *
import sys
import requests
import json

ACCOUNT = sys.argv[1]
PASSWORD = sys.argv[2]


print("Launching iTunes...")
webAddress = "http://192.168.0.210"

def initITunes():
    subprocess.call('taskkill /f /im APSDaemon*', shell=True)
    subprocess.call('taskkill /f /im iTunes*', shell=True)

    app = Application().start(r"C:\Program Files\iTunes\iTunes.exe")
    app.wait_cpu_usage_lower(10)
    time.sleep(8)

    def debugTopWin():
        topwin = app.top_window().wait('exists')
        texts = []
        texts += topwin.texts()
        for c in topwin.iter_children():
            texts += c.texts()
        print("-- Cur top win: %s, texts: %s" % (topwin, texts))
        return "-- Cur top win: %s, texts: %s" % (topwin, texts)

    def cleanAllDialog():
        while True:
            topwin = app.top_window().wait('exists')
            if 'Dialog' in topwin.class_name():
                print("    Closing dialog %s" % topwin.window_text())
                app.top_window().Button0.click()
            elif 'Tour' in topwin.window_text():
                print("    Closing Window %s" % topwin.window_text())
                topwin.close()
            else:
                break
            
            app.wait_cpu_usage_lower(10)
            time.sleep(5)

    # Click all first-time dialogs (like License Agreements, missing audios)
    cleanAllDialog()

    # Calm down a bit before main window operations
    app.wait_cpu_usage_lower(10)
    debugTopWin()

    # Click main window's first-time question ("No thanks" button)
    try:
        buttonText = app.iTunes.Button11.wait('ready').window_text()
        print('Button11 text is: %s' % buttonText)
        if 'Search' not in buttonText:
            print("Clicked 'No Thanks' Button!")
            app.iTunes.Button11.click_input()
            app.wait_cpu_usage_lower(10)
            time.sleep(4)
        else:
            raise Exception('stub')
    except:
        print("Not founding 'No Thanks' Button, passing on...")


    # Start logging in by clicking toolbar menu "Account"
    print("Clicking Account menu...")
    app.iTunes.Application.Static3.click()
    app.wait_cpu_usage_lower(10)
    time.sleep(3)

    debugTopWin()

    # Detect whether we have "&S" in popup, which refers to "Sign in"
    popup = app.PopupMenu
    if '&S' not in popup.menu().item(1).text():
        popup.close()
        return
        # raise Exception("Already logged in!")
    
    print("Signin menu presented, clicking to login!")
    # not log in
    popup.menu().item(1).click_input()
    app.wait_cpu_usage_lower(10)
    time.sleep(8)
    debugTopWin()

    for i in range(15):
        dialog = app.top_window()
        dialogWrap = dialog.wait('ready')
        assert dialogWrap.friendly_class_name() == 'Dialog'
        print("friendly_class_name is %s" % dialogWrap.friendly_class_name())
        time.sleep(1.0)
        try:
            if dialogWrap.window_text() == 'iTunes' \
                and dialog.Edit1.wait('ready').window_text() == 'Apple ID' \
                and dialog.Edit2.wait('ready').window_text() == 'Password' \
                and dialog.Button1.wait('exists').window_text() == '&Sign In':
                break
        except Exception as e:
            continue
    else:
        raise Exception("Failed to find login window in 15 iterations!")
    app.wait_cpu_usage_lower(10)

    print("Setting login dialog edit texts")

    appleid_Edit = dialog.Edit1
    appleid_Edit.wait('ready')
    appleid_Edit.click_input()
    appleid_Edit.type_keys(ACCOUNT)
    appleid_Edit.set_edit_text(ACCOUNT)
    time.sleep(3)

    pass_Edit = dialog.Edit2
    pass_Edit.wait('ready')
    pass_Edit.click_input()
    pass_Edit.type_keys(PASSWORD)
    pass_Edit.set_edit_text(PASSWORD)
    time.sleep(3)
    
    print("Clicking login button!")
    loginButton = dialog.Button1
    loginButton.wait('ready')
    # click multiple times as pywinauto seems to have some bug
    loginButton.click()
    time.sleep(0.5)
    try:
        loginButton.click()
        time.sleep(0.5)
        loginButton.click_input()
    except:
        pass
    

    print("Waiting login result...")
    time.sleep(10)
    debugText = debugTopWin()
    
    if "Sign In to the iTunes Store" in debugText:
        raise Exception("Failed to trigger Login button!")
    elif app.top_window().window_text() == 'Verification Failed':
        raise Exception("Verification Failed: %s" % app.top_window().Static2.window_text())


    print("Check 2FA auth...")
    need2FA = False
    for i in range(5):
        winText = debugTopWin()
        if "Enter the verification code sent to your other devices." in winText:
            print("need 2FA auth")
            need2FA = True
            dialog = app.top_window()
            dialogWrap = dialog.wait('ready')
            break
        else:
            print("check 2FA auth sleep 3s")
            time.sleep(3.0)
    
    
        # dialog = app.top_window()
        # dialogWrap = dialog.wait('ready')
        # assert dialogWrap.friendly_class_name() == 'Dialog'
        # print("2FA friendly_class_name is %s" % dialogWrap.friendly_class_name())
        # time.sleep(1.0)
        # try:
            # if dialogWrap.window_text() == 'iTunes' \
                # and dialog.Button1.wait('exists').window_text() == 'Continue':
                # print("need 2FA auth 1")
                # need2FA = true
                # break
        # except Exception as e:
            # continue
    # else:
    #     raise Exception("Failed to find 2FA window in 15 iterations!")
    app.wait_cpu_usage_lower(10)

    if need2FA == True:
        print("need 2FA")
    else:
        print("not need 2FA")
    
    if need2FA == True:
        print("Start request 2FA from web")
        for i in range(12):
            url = webAddress + '/request2FA'
            responseData = requests.get(url)
            jsonData = json.loads(responseData.text)
            twoFACode = jsonData["two_fa_code"]
            twoFACode = jsonData["two_fa_code"]
            twoFACode = jsonData["two_fa_code"]
            print("web 2FA is:%s" % twoFACode)
            
            if len(twoFACode) == 6:
                break
            
            print("not read 2FA from web, sleep 10s ,2FA len： %d" % len(twoFACode))
            time.sleep(10.0)
        else:
            raise Exception("not read 2FA in 15 iterations!")
        
        twoFA1 = twoFACode[0]
        twoFA2 = twoFACode[1]
        twoFA3 = twoFACode[2]
        twoFA4 = twoFACode[3]
        twoFA5 = twoFACode[4]
        twoFA6 = twoFACode[5]
        
        print("Setting 2FA dialog edit texts")
        
        twoFA_Edit1 = dialog.Edit1
        twoFA_Edit1.wait('ready')
        twoFA_Edit1.click_input()
        twoFA_Edit1.type_keys(twoFA1)
        twoFA_Edit1.set_edit_text(twoFA1)
        time.sleep(1)

        twoFA_Edit2 = dialog.Edit2
        twoFA_Edit2.wait('ready')
        twoFA_Edit2.click_input()
        twoFA_Edit2.type_keys(twoFA2)
        twoFA_Edit2.set_edit_text(twoFA2)
        time.sleep(1)
        
        twoFA_Edit3 = dialog.Edit3
        twoFA_Edit3.wait('ready')
        twoFA_Edit3.click_input()
        twoFA_Edit3.type_keys(twoFA3)
        twoFA_Edit3.set_edit_text(twoFA3)
        time.sleep(1)
        
        twoFA_Edit4 = dialog.Edit4
        twoFA_Edit4.wait('ready')
        twoFA_Edit4.click_input()
        twoFA_Edit4.type_keys(twoFA4)
        twoFA_Edit4.set_edit_text(twoFA4)
        time.sleep(1)
        
        twoFA_Edit5 = dialog.Edit5
        twoFA_Edit5.wait('ready')
        twoFA_Edit5.click_input()
        twoFA_Edit5.type_keys(twoFA5)
        twoFA_Edit5.set_edit_text(twoFA5)
        time.sleep(1)
        
        
        twoFA_Edit6 = dialog.Edit6
        twoFA_Edit6.wait('ready')
        twoFA_Edit6.click_input()
        twoFA_Edit6.type_keys(twoFA6)
        twoFA_Edit6.set_edit_text(twoFA6)
        time.sleep(1)
        
        
        print("Clicking 2FA button!")
        loginButton = dialog.Button1
        loginButton.wait('ready')
        # click multiple times as pywinauto seems to have some bug
        loginButton.click()
        time.sleep(0.5)
        try:
            loginButton.click()
            time.sleep(0.5)
            loginButton.click_input()
        except:
            pass
            
            
        print("Waiting 2FA result...")
        time.sleep(10)
        debugTopWin()

        if app.top_window().handle == dialogWrap.handle:
            raise Exception("Failed to trigger 2FA button!")
        elif app.top_window().window_text() == 'Verification Failed':
            raise Exception("Verification Failed: %s" % app.top_window().Static2.window_text())
    
    app.wait_cpu_usage_lower(10)

    # Finish & Cleanup
    print("Waiting all dialogs to finish")
    time.sleep(5)
    cleanAllDialog()


for init_i in range(3):
    try:
        initITunes()
        break
    except Exception as e:
        print("Init iTunes %d: Failed with %s" % (init_i, e))
        import traceback; traceback.print_exc()
        time.sleep(8)

print("Init iTunes Successfully!")