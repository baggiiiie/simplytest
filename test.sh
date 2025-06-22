python -m pytest --alluredir allure-results --clean-alluredir &&
    allure generate --clean &&
    allure serve
