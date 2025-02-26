package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"sync"
	"time"
)

const (
	url        = "http://speedtest.tele2.net/100MB.zip" // 替换为你想要测试的大文件 URL
	outputFile = "downloaded_file.zip"                  // 下载文件的保存路径
	maxRetries = 3                                      // 最大重试次数
)

func downloadFile(wg *sync.WaitGroup, ch chan float64) {
	defer wg.Done()

	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	var speed float64
	for i := 0; i < maxRetries; i++ {
		startTime := time.Now()

		resp, err := client.Get(url)
		if err != nil {
			fmt.Printf("请求失败 (尝试 %d): %v\n", i+1, err)
			continue
		}
		defer resp.Body.Close()

		file, err := os.Create(outputFile)
		if err != nil {
			fmt.Printf("创建文件失败: %v\n", err)
			return
		}
		defer file.Close()

		written, err := io.Copy(file, resp.Body)
		if err != nil {
			fmt.Printf("写入文件失败 (尝试 %d): %v\n", i+1, err)
			continue
		}

		endTime := time.Now()
		duration := endTime.Sub(startTime).Seconds()
		speed = float64(written) / (1024 * 1024) / duration // MB/s
		break
	}

	ch <- speed
}

func main() {
	var wg sync.WaitGroup
	ch := make(chan float64, 1)

	wg.Add(1)
	go downloadFile(&wg, ch)

	wg.Wait()
	close(ch)

	for speed := range ch {
		if speed > 0 {
			fmt.Printf("下载完成！\n")
			fmt.Printf("平均下载速度: %.2f MB/s\n", speed)
		} else {
			fmt.Println("所有尝试均失败，请检查网络连接或服务器状态。")
		}
	}
}
