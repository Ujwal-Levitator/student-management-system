import pickle
class Student:
    def __init__(self,roll_no,name,age,address,parent_name,parent_phone,previous_result,test_marks):
        self.roll_no=roll_no
        self.name=name
        self.age=age
        self.address=address
        self.parent_name=parent_name
        self.parent_phone=parent_phone
        self.previous_result=previous_result
        self.test_marks=test_marks
    def show_info(self):
        print('ROLL NUMBER:',self.roll_no)
        print('NAME:',self.name)
        print('AGE:',self.age)
        print('ADDRESS:',self.address)
        print('PARENT NAME:',self.parent_name)
        print('PARENT PHONE:',self.parent_phone)
        print('PREVIOUS PERCENTAGE:',self.previous_result)
        print('TEST MARKS:',self.test_marks)  
class Classroom:
    def __init__(self):
        self.students=[]
        self.next_roll_no=1
        self.load_details()
    def add_student(self,student):
        self.students.append(student)
        print('STUDENT ADDED SUCCESSFULLY')
        print('ASSIGNED ROLL NUMBER: ',student.roll_no)
    def display_all_students(self):
        if len(self.students)==0:
            print('there are no students in this classroom')
        else:
            print('REG NO.  ','NAME')
            for student in self.students:
                print(student.roll_no,'----',student.name)
    def remove_student(self,num):
        for student in self.students:
            if student.roll_no==num:
                self.students.remove(student)
                print('STUDENT REMOVED SUCCESSFULLY')
                return
        print('THERE IS NO STUDENT WITH THE ROLLNUMBER',num,'IN THIS CLASSROOM')
    def total_students(self):
        print('THE TOTAL NUMBER OF STUDENT IN THE CLASS ROOM:',len(self.students))
    def show_student_details(self,num):
        for student in self.students:
            if student.roll_no==num:
                student.show_info()
                return
        print('THERE IS NO STUDENT WITH THE ROLLNUMBER',num,'IN THIS CLASSROOM')
    def save_details(self):
        with open ('student_details.dat','wb') as file:
            data={'students':self.students,'next_roll_no':self.next_roll_no}
            pickle.dump(data,file)
        print()
    def load_details(self):
        try:
            with open ('student_details.dat','rb') as file:
                data=pickle.load(file)
                self.students=data['students']
                self.next_roll_no=data['next_roll_no']
        except FileNotFoundError:
            self.students=[]
            self.next_roll_no=1
        except EOFError:
            self.students=[]
            self.next_roll_no=1
classroom1=Classroom()        
while True:
    try:
        print('===========STUDENT MANAGEMENT SYSTEM=============')
        print()
        print('1. Add student')
        print('2. Show All Students')
        print('3. Show Student Details')
        print('4. Remove Student')
        print('5. Total students')
        print('6. Exit')
        print()
        ch=int(input('PLEASE ENTER AN APPROPRIATE CHOICE: '))
        if ch==6:
            classroom1.save_details()
            print()
            print()
            print('========THANK YOU===========')
            print()
            print()
            break
        elif ch==1:
            print()
            print()
            print('========STUDENT ADDING INTERFACE===========')
            name=input('ENTER NAME: ')
            age=int(input('ENTER AGE: '))
            address=input('ENTER ADDRESS: ')
            parent_name=input('ENTER PARENT NAME: ')
            parent_phone=input('ENTER PARENT PHONE NO.: ')
            if len(parent_phone)!=10:
                print('PHONE NUMBER LENGTH SHOULD BE 10 CHARACTERS')
            else:
                previous_result=input('ENTER PREVIOUS RESULT(pass/fail): ')
                test_marks=input('ENTER TEST MARKS: ')
                student=Student(classroom1.next_roll_no,name,age,address,parent_name,parent_phone,previous_result,test_marks)
                classroom1.add_student(student)
                classroom1.next_roll_no+=1
                print()
                print()
        elif ch==2:
            print()
            print()
            print('==========DISPLAYING ALL STUDENTS===========')
            classroom1.display_all_students()
            print()
            print()
        elif ch==3:
            print()
            print()
            print('=========STUDENT DETAILS INTERFACE==========')
            num=int(input('ENTER THE ROLL NUMBER OF THE STUDENT: '))
            classroom1.show_student_details(num)
            print()
            print()
        elif ch==4:
            print()
            print()
            print('==========STUDENT REMOVAL INTERFACE=============')
            num=int(input('ENTER THE ROLL NUMBER OF THE STUDENT: '))
            classroom1.remove_student(num)
            print()
            print()
        elif ch==5:
            print()
            print()
            classroom1.total_students()
            print()
            print()
        else:
            print('PLEASE ENTER AN APPROPRIATE CHOICE')
    except ValueError:
        print('PLEASE ENTER APPROPRIATE DETAILS')