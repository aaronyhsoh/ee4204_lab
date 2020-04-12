/**********************************
tcp_ser.c: the source file of the server in tcp transmission 
***********************************/

#include "headsock.h"
#include <time.h>
#include <errno.h>    

int msleep(long msec)
{
    struct timespec ts;
    int res;

    if (msec < 0)
    {
        errno = EINVAL;
        return -1;
    }

    ts.tv_sec = msec / 1000;
    ts.tv_nsec = (msec % 1000) * 1000000;

    do {
        res = nanosleep(&ts, &ts);
    } while (res && errno == EINTR);

    return res;
}

#define BACKLOG 10
int msleep(long msec);
void str_ser(int sockfd, struct sockaddr *addr, int len, int error_prob);                                                        // transmitting and receiving function

int main(int argc, char **argv)
{
	int sockfd, con_fd, ret;
	struct sockaddr_in my_addr;
	struct sockaddr_in their_addr;
	int sin_size;
	int error_prob;
	
	if (argc != 2) {
		printf("parameters do not match");
	}
	
	error_prob = atoi(argv[1]);

//	char *buf;
	pid_t pid;

	sockfd = socket(AF_INET, SOCK_DGRAM, 0);          //create socket
	if (sockfd <0)
	{
		printf("error in socket!");
		exit(1);
	}
	
	my_addr.sin_family = AF_INET;
	my_addr.sin_port = htons(MYUDP_PORT);
	my_addr.sin_addr.s_addr = htonl(INADDR_ANY);//inet_addr("172.0.0.1");
	bzero(&(my_addr.sin_zero), 8);
	ret = bind(sockfd, (struct sockaddr *) &my_addr, sizeof(struct sockaddr));                //bind socket
	if (ret <0)
	{
		printf("error in binding");
		exit(1);
	}
	
	ret = listen(sockfd, BACKLOG);                              //listen

	printf("Waiting for data\n");
	str_ser(sockfd, (struct sockaddr *)&my_addr, sizeof(struct sockaddr_in), error_prob);
	printf("SUCCESS");
	close(sockfd);
	exit(0);
}

void str_ser(int sockfd, struct sockaddr *addr, int len, int error_prob)
{
	char buf[BUFSIZE];
	FILE *fp;
	char recvs[DATALEN];
	struct ack_so ack;
	int end, n = 0;
	long lseek=0;
	end = 0;
	int numPackets = 0;
	int randNum;
	
	printf("receiving data!\n");

	while(!end)
	{
		if ((n= recvfrom(sockfd, &recvs, DATALEN, 0, addr, (socklen_t *)&len))==-1)                                   //receive the packet
		{
			printf("error when receiving\n");
			//ack.num = -1;
		}
		if (recvs[n-1] == '\0')									//if it is the end of the file
		{
			end = 1;
			n --;
		}
		
		randNum = rand() % 100 + 1;
		printf("random: %d\n", randNum);
		
		printf("n: %d\n", n);
		memcpy((buf+lseek), recvs, n);
		if (randNum < error_prob) {
			ack.num = 0;
			ack.len = 0;
			end = 0;
		} else {
			ack.num = 1;
			ack.len = 0;
			lseek += n;
		}
		
		if ((n = sendto(sockfd, &ack, 2, 0, addr, len)==-1))
		{
			printf("send error!");								//send the ack
			exit(1);
		}
		printf("Num packets: %d\n", numPackets);
		numPackets++;
		//msleep(50);
	}
	
	if ((fp = fopen ("myUDPreceive.txt","wt")) == NULL)
	{
		printf("File doesn't exit\n");
		exit(0);
	}
	fwrite (buf , 1 , lseek , fp);					//write data into file
	fclose(fp);
	printf("a file has been successfully received!\nthe total data received is %d bytes\n", (int)lseek);
}
