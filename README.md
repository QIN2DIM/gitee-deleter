<p  align="center"><img width="80%" src="https://user-images.githubusercontent.com/62018067/169050956-8fb236bd-0874-4a17-ab9c-ace839b490b4.png"></p>


## Introduction
[Gitee](https://gitee.com/) 销号[砖]家，一键删光「我的仓库」。

## Requirements

- google-chrome
- Python3.8+

## Usage

> 项目依赖 [google-chrome](https://www.google.com/intl/zh-CN/chrome/) 运行，请确保你的计算机已装有谷歌浏览器。

1. 下载依赖

   ```bash
   pip install gitee-deleter
   ```

2. 六根清净方为道，退步原来是向前

   拷贝如下参考代码，填入必要的账号信息，启动有头浏览器进行自动化作业。

   「删库」是相当敏感的操作，所以本人在不影响脚本性能的情况下插入了非常多的 `sleep` 语句。如果你发现情况不对，手动关闭浏览器杀死进程即可。

   ```python
   from gitee_deleter import remove_all
   
   GITEE_USERNAME: str = ""
   GITEE_PASSWORD: str = ""
   
   if __name__ == "__main__":
       remove_all(username=GITEE_USERNAME, password=GITEE_PASSWORD)
   
   ```
