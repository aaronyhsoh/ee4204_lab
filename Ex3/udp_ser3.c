/**********************************
tcp_ser.c: the source file of the server in tcp transmission 
***********************************/

#include "headsock.h"

#define BACKLOG 10

void str_ser(int sockfd, struct sockaddr *addr, int len);                                                        // transmitting and receiving function

int main(void)
{
	int sockfd, con_fd, ret;
	struct sockaddr_in my_addr;
	struct sockaddr_in their_addr;
	int sin_size;

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
	str_ser(sockfd, (struct sockaddr *)&my_addr, sizeof(struct sockaddr_in));
	printf("SUCCESS");
	close(sockfd);
	exit(0);
}

void str_ser(int sockfd, struct sockaddr *addr, int len)
{
	char buf[BUFSIZE];
	FILE *fp;
	char recvs[DATALEN];
	struct ack_so ack;
	int end, n = 0;
	long lseek=0;
	end = 0;
	int numPackets = 0;
	
	printf("receiving data!\n");

	while(!end)
	{
		if ((n= recvfrom(sockfd, &recvs, DATALEN, 0, addr, (socklen_t *)&len))==-1)                                   //receive the packet
		{
			printf("error when receiving\n");
			exit(1);
		}
		if (recvs[n-1] == '\0')									//if it is the end of the file
		{
			end = 1;
			n --;
		}
		memcpy((buf+lseek), recvs, n);
		ack.num = 1;
		ack.len = 0;
		if ((n = sendto(sockfd, &ack, 2, 0, addr, len)==-1))
		{
			printf("send error!");								//send the ack
			exit(1);
		}
		lseek += n;
		printf("Num packets: %d\n", numPackets);
		numPackets++;
	}
	
	if ((fp = fopen ("myTCPreceive.txt","wt")) == NULL)
	{
		printf("File doesn't exit\n");
		exit(0);
	}
	fwrite (buf , 1 , lseek , fp);					//write data into file
	fclose(fp);
	printf("a file has been successfully received!\nthe total data received is %d bytes\n", (int)lseek);
}
